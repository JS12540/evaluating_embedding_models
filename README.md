# Embedding Evaluation Toolkit

## Setup
1. Create a virtualenv and install requirements:
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Place the source DOCX (ACME_Enterprise_Platform.docx) in the project folder.

3. Export API keys:
   export OPENAI_API_KEY="sk-..."
   export COHERE_API_KEY="... (if using cohere)"

## Run
- Generate chunks and queries (will create chunks.csv and queries.csv):
  python runner.py --docx ACME_Enterprise_Platform.docx

- To run only certain models:
  python runner.py --models openai cohere

- Outputs are saved under `outputs/`:
  - `{model}_retrievals.json` (top-k chunk ids per query)
  - `{model}_per_query_metrics.csv` (detailed per-query metrics)
  - `{model}_agg_metrics.csv` (aggregated metrics across queries)
  - `summary_metrics.json` (aggregate metrics for all models)

## Notes
- Ensure `queries.csv` has a `gt_chunk_ids` column containing JSON lists of correct chunk ids for each query.
- The chunker is naive; for production you may want to use semantic chunking and preserve headings/metadata.
- For statistical significance testing, compute per-query MRRs for each model and run paired tests (bootstrap or Wilcoxon).
