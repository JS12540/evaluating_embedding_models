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
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

DATA_PATH = "data/structured_acme_ground_dataset.csv"
CHUNKS_PATH = "data/chunks.json"
INDEX_PATHS = {
    "openai": "embeddings/openai.index",
    "cohere": "embeddings/cohere.index",
    "open_source": "embeddings/open_source.index"
}
TOP_K = 5

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
co = cohere.Client(os.getenv("COHERE_API_KEY"))
hf_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

openai_model = "text-embedding-3-small"
cohere_model = "embed-v4.0"

chunks = json.load(open(CHUNKS_PATH, "r", encoding="utf-8"))
chunk_id_to_text = {c["metadata"]["chunk_id"]: c["content"] for c in chunks}
chunk_ids = list(chunk_id_to_text.keys())

ground_truth = pd.read_csv(DATA_PATH)

def embed_openai(text):
    resp = openai_client.embeddings.create(model=openai_model, input=[text])
    return np.array(resp.data[0].embedding, dtype="float32")

def embed_cohere(text):
    resp = co.embed(texts=[text], model=cohere_model)
    return np.array(resp.embeddings[0], dtype="float32")

def embed_hf(text):
    return np.array(hf_model.encode([text])[0], dtype="float32")

def recall_at_k(true_ids, retrieved_ids, k):
    retrieved_topk = retrieved_ids[:k]
    return len(set(true_ids) & set(retrieved_topk)) / len(true_ids)

def precision_at_k(true_ids, retrieved_ids, k):
    retrieved_topk = retrieved_ids[:k]
    return len(set(true_ids) & set(retrieved_topk)) / k

def mrr(true_ids, retrieved_ids):
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in true_ids:
            return 1 / rank
    return 0.0

def ndcg_at_k(true_ids, retrieved_ids, k):
    dcg, idcg = 0.0, 0.0
    for i, rid in enumerate(retrieved_ids[:k]):
        if rid in true_ids:
            dcg += 1 / np.log2(i + 2)
    idcg = sum(1 / np.log2(i + 2) for i in range(min(len(true_ids), k)))
    return dcg / idcg if idcg > 0 else 0.0

# ========= LOAD FAISS INDICES =========
indices = {name: faiss.read_index(path) for name, path in INDEX_PATHS.items()}

def load_embeddings_from_faiss(index, dim, texts):
    # For similarity computation FAISS only stores vectors, not ids → we rely on order.
    # chunks were added in same order as chunks.json
    xb = np.array([index.reconstruct(i) for i in range(index.ntotal)])
    return xb

dim = 1024  # dynamic detection could be added
embeddings = {m: load_embeddings_from_faiss(idx, dim, chunk_id_to_text) for m, idx in indices.items()}

results = []

for model_name, emb_matrix in embeddings.items():
    print(f"\nEvaluating model: {model_name.upper()}")
    index = indices[model_name]
    metrics = {"recall@3": [], "recall@5": [], "precision@3": [], "mrr": [], "ndcg@5": []}

    for _, row in tqdm(ground_truth.iterrows(), total=len(ground_truth)):
        q = row["question"]
        gt_chunks = ast.literal_eval(row["chunks"])

        true_ids = [c["chunk_id"] for c in gt_chunks]

        if model_name == "openai":
            q_emb = embed_openai(q)
        elif model_name == "cohere":
            q_emb = embed_cohere(q)
        else:
            q_emb = embed_hf(q)

        q_emb = np.array(q_emb).reshape(1, -1)
        D, I = index.search(q_emb, TOP_K)
        retrieved_ids = [chunk_ids[i] for i in I[0]]

        metrics["recall@3"].append(recall_at_k(true_ids, retrieved_ids, 3))
        metrics["recall@5"].append(recall_at_k(true_ids, retrieved_ids, 5))
        metrics["precision@3"].append(precision_at_k(true_ids, retrieved_ids, 3))
        metrics["mrr"].append(mrr(true_ids, retrieved_ids))
        metrics["ndcg@5"].append(ndcg_at_k(true_ids, retrieved_ids, 5))

    summary = {m: np.mean(v) for m, v in metrics.items()}
    results.append({"model": model_name, **summary})

df_results = pd.DataFrame(results)
print("\nEvaluation Results:")
print(df_results.to_string(index=False))

df_results.to_csv("evaluation_results.csv", index=False)
print("\nSaved detailed results to evaluation_results.csv")
