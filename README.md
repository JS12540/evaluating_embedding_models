# Embedding Evaluation Toolkit

## Setup

### 1. Create a virtual environment and install requirements
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Place the source DOCX

Place the source DOCX (e.g., `ACME_Enterprise_Platform.docx`) in the `data/` folder.

### 3. Export API keys
```bash
export OPENAI_API_KEY="sk-..."
export COHERE_API_KEY="..."
```

## Chunking Strategies

This toolkit supports two types of chunking:

### 1. Structured Chunking

- Based on the document's table of contents (headings hierarchy)
- Preserves sections and sub-sections to retain context and meaning
- Run using:
```bash
python structured_chunking.py
```

- Results are stored in `data/`

### 2. Recursive Character Chunking

- Splits the document into chunks based on a recursive character-based strategy (useful for very long paragraphs or text-heavy documents)
- Run using:
```bash
python recursive_chunking.py
```

- Results are stored in `data/`

## Ground Truth Generation

Ground truth chunks per query can be generated using:
```bash
python generate_ground_truth.py
```

- Make sure results are in the `data/` folder for proper storage
- To send full chunks to LLMs, we use **TOON — Token Object Oriented Notation**:

### What is TOON?

TOON is a modern, lightweight data format optimized for LLMs — think of it as **"JSON, reimagined for token efficiency and human readability."**

It eliminates syntactic overhead by:
- Removing curly braces, square brackets, and quotes
- Using indentation and tabular patterns instead
- Declaring keys once per table-like block
- Replacing commas/braces with clean structure

### Why TOON Helps

When sending data to LLMs:
- **Traditional JSON** wastes tokens on punctuation, repeated keys, and verbose syntax
- **TOON** maintains data clarity while cutting syntactic noise

**Result:** 30–60% fewer tokens on average, reducing API costs and improving processing efficiency.


## Embedding Models

We support embeddings from three models:

### 1. OpenAI
- **Model:** `text-embedding-3-small`
- **Description:** General-purpose, high-quality embeddings for semantic similarity tasks

### 2. Cohere
- **Model:** `embed-v4.0`
- **Description:** Robust embeddings optimized for retrieval and semantic search

### 3. Hugging Face
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (via `SentenceTransformer`)
- **Description:** Lightweight, fast, and efficient embeddings for smaller-scale retrieval tasks

## Evaluation

To evaluate embeddings, run:
```bash
python evaluate_models.py
```

### Metrics Calculated

To evaluate retrieval accuracy, ranking quality, and relevance, this toolkit uses:

| Metric | What It Measures | How It's Calculated | Why It Matters |
|--------|------------------|---------------------|----------------|
| **Precision@3** | Fraction of retrieved chunks that are relevant in top-3 | `(# relevant chunks in top-3) / 3` | Shows how "clean" the top 3 results are - critical for RAG where only top results are used. |
| **Recall@3** | Fraction of all relevant chunks found within top-3 | `(# relevant chunks in top-3) / (total # relevant chunks)` | Measures coverage of relevant information in top-3 results. |
| **Precision@5** | Fraction of retrieved chunks that are relevant in top-5 | `(# relevant chunks in top-5) / 5` | Assesses result quality with a slightly larger retrieval window. |
| **Recall@5** | Fraction of all relevant chunks found within top-5 | `(# relevant chunks in top-5) / (total # relevant chunks)` | Shows if expanding to 5 results captures more relevant information. |
| **MRR** (Mean Reciprocal Rank) | Average of reciprocal ranks of first relevant chunk | `1 / (rank of first relevant chunk)`, averaged across queries | Captures ranking quality — whether the top hit is correct. Ranges from 0 to 1, where 1 means the first result is always relevant. |
| **nDCG@5** (Normalized Discounted Cumulative Gain) | Quality of ranking accounting for position of relevant chunks | `DCG@5 / IDCG@5` where higher-ranked relevant docs contribute more | Rewards systems that place relevant chunks higher in rankings. Accounts for graded relevance when multiple chunks matter. |

### Metric Interpretation
- **Precision** and **Recall** are complementary: high precision means few false positives, high recall means few false negatives.
- **MRR** is especially important when users typically look at only the first relevant result.
- **nDCG@5** provides a nuanced view by considering both whether relevant chunks are retrieved AND how highly they're ranked.
- Compare metrics at k=3 vs k=5 to understand how retrieval quality changes with window size.


Evaluations are done per question and aggregated for both chunking strategies.

## Results

### Recursive Chunking Evaluation Results

| model        | recall@3 | recall@5 | precision@3 | precision@5 | mrr    | ndcg@3 | ndcg@5 |
|--------------|----------|----------|-------------|-------------|--------|--------|--------|
| openai       | 0.6333   | 0.80     | 0.5333      | 0.40        | 0.75   | 0.6325 | 0.7021 |
| cohere       | 0.70     | 0.80     | 0.60        | 0.40        | 0.8667 | 0.7370 | 0.7641 |
| open_source  | 0.45     | 0.70     | 0.40        | 0.36        | 0.75   | 0.4938 | 0.6173 |

### Structured Chunking Evaluation Results

| model        | recall@3 | recall@5 | precision@3 | precision@5 | mrr    | ndcg@3 | ndcg@5 |
|--------------|----------|----------|-------------|-------------|--------|--------|--------|
| openai       | 0.7833   | 0.90     | 0.60        | 0.44        | 1.00   | 0.8757 | 0.9161 |
| cohere       | 0.6833   | 0.75     | 0.5333      | 0.36        | 1.00   | 0.7983 | 0.8051 |
| open_source  | 0.6833   | 0.75     | 0.5333      | 0.36        | 0.8667 | 0.7370 | 0.7438 |

## Summary

**Structured chunking consistently outperforms recursive character chunking** across recall, MRR, and nDCG metrics.

**Reason:** Structured chunking preserves context and document hierarchy, which improves retrieval relevance and ranking. Recursive chunking, while flexible, may split semantically linked sentences or sections, lowering relevance.

## Improving Retrieval Accuracy

To further improve retrieval:

### 1. Metadata Filtering
- Filter chunks using headings, section names, dates, or tags to reduce search space and improve precision
- **Example:** Only search within "Implementation" or "API Reference" sections

### 2. Knowledge Graphs
- Link entities and concepts in chunks to a graph to improve semantic retrieval
- Allows retrieval based on relationships, not just keywords or embeddings

### 3. Hybrid Search
- Combine vector search + keyword/metadata filters
- Vector search captures semantic meaning, filters ensure domain specificity

### 4. Query Expansion
- Automatically expand queries with synonyms or related terms to increase recall