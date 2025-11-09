# Embedding Evaluation Toolkit

## Setup
1. Create a virtualenv and install requirements:
```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```

2. Place the source DOCX (ACME_Enterprise_Platform.docx) in the project folder.

3. Export API keys:
```bash
   export OPENAI_API_KEY="sk-..."
   export COHERE_API_KEY="... (if using cohere)"
```

# Embedding Evaluation Toolkit

## Setup
1. Create a virtualenv and install requirements:
```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```

2. Place the source DOCX (ACME_Enterprise_Platform.docx) in the project folder.

3. Export API keys:
```bash
   export OPENAI_API_KEY="sk-..."
   export COHERE_API_KEY="... (if using cohere)"
```

## Recommended Metrics & Why

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

## Run
- Generate chunks and queries (will create chunks.csv and queries.csv):
```bash
  python runner.py --docx ACME_Enterprise_Platform.docx
```

- To run only certain models:
```bash
  python runner.py --models openai cohere
```

- Outputs are saved under `outputs/`:
  - `{model}_retrievals.json` (top-k chunk ids per query)
  - `{model}_per_query_metrics.csv` (detailed per-query metrics)
  - `{model}_agg_metrics.csv` (aggregated metrics across queries)
  - `summary_metrics.json` (aggregate metrics for all models)

## Notes
- Ensure `queries.csv` has a `gt_chunk_ids` column containing JSON lists of correct chunk ids for each query.
- The chunker is naive; for production you may want to use semantic chunking and preserve headings/metadata.
- For statistical significance testing, compute per-query MRRs for each model and run paired tests (bootstrap or Wilcoxon).
## Run
- Generate chunks and queries (will create chunks.csv and queries.csv):
```bash
  python runner.py --docx ACME_Enterprise_Platform.docx
```

- To run only certain models:
```bash
  python runner.py --models openai cohere
```

- Outputs are saved under `outputs/`:
  - `{model}_retrievals.json` (top-k chunk ids per query)
  - `{model}_per_query_metrics.csv` (detailed per-query metrics)
  - `{model}_agg_metrics.csv` (aggregated metrics across queries)
  - `summary_metrics.json` (aggregate metrics for all models)

## Notes
- Ensure `queries.csv` has a `gt_chunk_ids` column containing JSON lists of correct chunk ids for each query.
- The chunker is naive; for production you may want to use semantic chunking and preserve headings/metadata.
- For statistical significance testing, compute per-query MRRs for each model and run paired tests (bootstrap or Wilcoxon).