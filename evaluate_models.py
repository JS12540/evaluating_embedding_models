import os
import json
import faiss
import ast
import numpy as np
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
import cohere
from sentence_transformers import SentenceTransformer

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
co = cohere.Client(os.getenv("COHERE_API_KEY"))

CHUNKS_PATH = "data/chunks.json"
GROUND_PATH = "data/structured_acme_ground_dataset.csv"
INDEX_PATHS = {
    "openai": "embeddings/openai.index",
    "cohere": "embeddings/cohere.index",
    "open_source": "embeddings/open_source.index"
}
TOP_K = 5

hf_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
openai_model = "text-embedding-3-small"
cohere_model = "embed-v4.0"

chunks = json.load(open(CHUNKS_PATH, "r", encoding="utf-8"))
chunk_id_to_text = {c["metadata"]["chunk_id"]: c["content"] for c in chunks}
chunk_ids = list(chunk_id_to_text.keys())
ground_truth = pd.read_csv(GROUND_PATH)

def embed_openai(text):
    resp = openai_client.embeddings.create(model=openai_model, input=[text])
    return np.array(resp.data[0].embedding, dtype="float32")

def embed_cohere(text):
    resp = co.embed(texts=[text], model=cohere_model)
    return np.array(resp.embeddings[0], dtype="float32")

def embed_hf(text):
    return np.array(hf_model.encode([text])[0], dtype="float32")

def recall_at_k(true_ids, retrieved_ids, k):
    return len(set(true_ids) & set(retrieved_ids[:k])) / len(true_ids) if len(true_ids) > 0 else 0.0

def precision_at_k(true_ids, retrieved_ids, k):
    return len(set(true_ids) & set(retrieved_ids[:k])) / k if k > 0 else 0.0

def mrr(true_ids, retrieved_ids):
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in true_ids:
            return 1 / rank
    return 0.0

def ndcg_at_k(true_ids, retrieved_ids, k):
    dcg = sum(1 / np.log2(i + 2) for i, rid in enumerate(retrieved_ids[:k]) if rid in true_ids)
    idcg = sum(1 / np.log2(i + 2) for i in range(min(len(true_ids), k)))
    return dcg / idcg if idcg > 0 else 0.0

indices = {m: faiss.read_index(path) for m, path in INDEX_PATHS.items()}

all_model_results = []
all_question_records = []

for model_name, index in indices.items():
    print(f"\nEvaluating {model_name.upper()}...")
    metrics = {
        "recall@3": [], "recall@5": [],
        "precision@3": [], "precision@5": [],
        "mrr": [], "ndcg@3": [], "ndcg@5": []
    }

    for _, row in tqdm(ground_truth.iterrows(), total=len(ground_truth)):
        q = row["question"]

        try:
            gt_chunks = ast.literal_eval(row["chunks"])
        except Exception as e:
            print(f"⚠️ Parse error in row {row.get('question_id', '?')}: {e}")
            continue

        true_ids = [c["chunk_id"] for c in gt_chunks]

        if model_name == "openai":
            q_emb = embed_openai(q)
        elif model_name == "cohere":
            q_emb = embed_cohere(q)
        else:
            q_emb = embed_hf(q)

        D, I = index.search(np.array([q_emb]), TOP_K)
        retrieved_ids = [chunk_ids[i] for i in I[0]]
        retrieved_texts = [chunk_id_to_text[i] for i in retrieved_ids]

        metrics["recall@3"].append(recall_at_k(true_ids, retrieved_ids, 3))
        metrics["recall@5"].append(recall_at_k(true_ids, retrieved_ids, 5))
        metrics["precision@3"].append(precision_at_k(true_ids, retrieved_ids, 3))
        metrics["precision@5"].append(precision_at_k(true_ids, retrieved_ids, 5))
        metrics["mrr"].append(mrr(true_ids, retrieved_ids))
        metrics["ndcg@3"].append(ndcg_at_k(true_ids, retrieved_ids, 3))
        metrics["ndcg@5"].append(ndcg_at_k(true_ids, retrieved_ids, 5))

        question_record = {
            "model": model_name,
            "question_id": row.get("question_id", None),
            "question": q,
            "truth_chunks": [
                {"chunk_id": cid, "text": chunk_id_to_text[cid]}
                for cid in true_ids if cid in chunk_id_to_text
            ],
            "retrieved_chunks": [
                {"chunk_id": cid, "text": chunk_id_to_text[cid]}
                for cid in retrieved_ids if cid in chunk_id_to_text
            ],
            "recall@3": metrics["recall@3"][-1],
            "recall@5": metrics["recall@5"][-1],
            "precision@3": metrics["precision@3"][-1],
            "precision@5": metrics["precision@5"][-1],
            "mrr": metrics["mrr"][-1],
            "ndcg@3": metrics["ndcg@3"][-1],
            "ndcg@5": metrics["ndcg@5"][-1],
        }
        all_question_records.append(question_record)

    summary = {m: np.mean(v) for m, v in metrics.items()}
    summary["model"] = model_name
    all_model_results.append(summary)

df_models = pd.DataFrame(all_model_results)
df_questions = pd.DataFrame(all_question_records)

print("\nCombined Evaluation Results:")
print(df_models.to_string(index=False))

df_models.to_csv("evaluation_results.csv", index=False)
df_questions.to_csv("detailed_per_question_results.csv", index=False)

print("\nResults saved:")
print("  - evaluation_results.csv (summary per model)")
print("  - detailed_per_question_results.csv (per-question results)")
