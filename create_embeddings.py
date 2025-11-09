import os
import json
import faiss
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
import cohere
from sentence_transformers import SentenceTransformer

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not OPENAI_API_KEY or not COHERE_API_KEY:
    raise ValueError("Missing API keys! Please set OPENAI_API_KEY and COHERE_API_KEY in your .env file.")

CHUNKS_PATH = "data/acme_recursive_chunks_char.json"
INDEX_SAVE_PATH = "recursive_embeddings/"
BATCH_SIZE = 32

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

filtered_chunks = [c for c in chunks if c["content"].strip() != ""]
texts = [c["content"] for c in filtered_chunks]
metadata = [c["metadata"] for c in filtered_chunks]

# OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)
openai_model = "text-embedding-3-small"

# Cohere
co = cohere.Client(COHERE_API_KEY)
cohere_model = "embed-v4.0"

# Sentence Transformers
hf_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_openai(texts):
    """
    Generates OpenAI embeddings for a list of texts.

    Args:
        texts (list[str]): List of texts to generate embeddings for

    Returns:
        np.ndarray: A numpy array of shape (len(texts), 384) containing the OpenAI embeddings for each text
    """
    embeddings = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Generating OpenAI Embeddings"):
        batch = texts[i:i+BATCH_SIZE]
        response = openai_client.embeddings.create(model=openai_model, input=batch)
        embeddings.extend([d.embedding for d in response.data])
    return np.array(embeddings, dtype="float32")

def embed_cohere(texts):
    """
    Generates Cohere embeddings for a list of texts.

    Args:
        texts (list[str]): List of texts to generate embeddings for

    Returns:
        np.ndarray: A numpy array of shape (len(texts), 128) containing the Cohere embeddings for each text
    """
    embeddings = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Generating Cohere Embeddings"):
        batch = texts[i:i+BATCH_SIZE]
        resp = co.embed(texts=batch, model=cohere_model)
        embeddings.extend(resp.embeddings)
    return np.array(embeddings, dtype="float32")

def embed_hf(texts):
    """
    Generates SentenceTransformer embeddings for a list of texts.

    Args:
        texts (list[str]): List of texts to generate embeddings for

    Returns:
        np.ndarray: A numpy array of shape (len(texts), embedding_dim) containing the SentenceTransformer embeddings for each text
    """
    print("Generating SentenceTransformer Embeddings...")
    return np.array(hf_model.encode(texts, show_progress_bar=True), dtype="float32")

def build_faiss_index(embeddings, dim, path):
    """
    Builds a FAISS index from a set of embeddings and saves it to disk.

    Args:
        embeddings (np.ndarray): A numpy array of shape (n_samples, dim) containing the embeddings to index
        dim (int): The dimensionality of the embeddings
        path (str): The path to save the FAISS index to

    Returns:
        faiss.IndexFlatL2: The built FAISS index
    """
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, path)
    print(f"FAISS index saved to {path}")
    return index

if __name__ == "__main__":
    os.makedirs(INDEX_SAVE_PATH, exist_ok=True)

    print("Starting embedding generation...")

    # --- OpenAI ---
    openai_embeddings = embed_openai(texts)
    build_faiss_index(openai_embeddings, openai_embeddings.shape[1], os.path.join(INDEX_SAVE_PATH, "openai.index"))

    # --- Cohere ---
    cohere_embeddings = embed_cohere(texts)
    build_faiss_index(cohere_embeddings, cohere_embeddings.shape[1], os.path.join(INDEX_SAVE_PATH, "cohere.index"))

    # --- Sentence Transformers ---
    hf_embeddings = embed_hf(texts)
    build_faiss_index(hf_embeddings, hf_embeddings.shape[1], os.path.join(INDEX_SAVE_PATH, "open_source.index"))

    print("\nAll embeddings generated and saved successfully!")
