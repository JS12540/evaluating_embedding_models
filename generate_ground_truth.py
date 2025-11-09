import json
import csv
import os
import toon
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

INPUT_JSON = "data/acme_recursive_chunks_char.json"
OUTPUT_CSV = "ground_dataset.csv"
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.0

questions = {
    "Q1": "Describe the specific policies and controls available to prevent data loss and control information flow from the Acme application on unmanaged, employee-owned mobile devices. Detail how data can be contained within the application and what actions can be taken if a device is compromised or lost.",
    "Q2": "What is Acme's guiding architectural philosophy for security? Describe the core principles of this architecture, such as how it redefines the security perimeter and its approach to access control.",
    "Q3": "Our security operations team requires deep integration for monitoring user and administrative activity. Describe the platform's native capabilities for exporting detailed audit logs and the specific mechanisms or connectors provided for integration with enterprise Security Information and Event Management (SIEM) platforms.",
    "Q4": "For compliance purposes, we must enforce policies that actively prevent communication between specific user groups. What platform feature allows an administrator to create such a policy, and what is the user experience for individuals in groups where this communication control is enforced?",
    "Q5": "Beyond the governance of customer data used by AI features, what is Acme's framework for the responsible development of the AI models themselves? Specifically, what is your policy regarding the sourcing of training data for global models, and what governance processes are in place to validate models for fairness and bias before deployment?"
}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # requires OPENAI_API_KEY in your environment


def load_chunks(path):
    """Load and strip metadata; keep only chunk_id and text."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    simple_chunks = [{"chunk_id": c["metadata"]["chunk_id"], "text": c["content"]} for c in data]
    return simple_chunks


def build_prompt_toon(chunks):
    """Builds a token-efficient LLM prompt using TOON encoding."""
    # Convert chunks to TOON format
    toon_chunks = toon.encode(chunks)
    toon_questions = toon.encode(questions)

    system_msg = (
        "You are a precise dataset-labeling assistant. "
        "You must identify which documentation chunks directly and explicitly answer each question. "
        "Do NOT guess or infer. Select only chunks that clearly answer the question. "
        "Return strictly valid JSON (no prose or markdown)."
    )

    user_msg = f"""
You are given the following Acme documentation in TOON format.

<CONTEXT_CHUNKS_TOON>
{toon_chunks}
</CONTEXT_CHUNKS_TOON>

<QUESTIONS_TOON>
{toon_questions}
</QUESTIONS_TOON>

For each question:
- Identify only the relevant chunk IDs and texts that directly answer it.
- Return a JSON array of objects in this exact format:
[
  {{
    "question_id": "Q1",
    "question": "Full question text",
    "chunks": [{{"chunk_id": "chunk_97", "text": "..."}}],
    "rationale": "Plain-English reasoning"
  }},
  ...
]

Return only the JSON, no commentary.
    """
    return system_msg, user_msg


def call_model(system_msg, user_msg):
    """Calls the LLM with full TOON context."""
    print("Sending TOON-encoded dataset to model...")
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content


def parse_json_response(text):
    """Extracts JSON from model output robustly."""
    try:
        return json.loads(text)
    except Exception:
        import re
        m = re.search(r"(\[.*\])", text, re.S)
        if m:
            return json.loads(m.group(1))
        raise RuntimeError("Unable to parse JSON from model output.")


def write_csv(data, outpath):
    """Write the parsed dataset into a CSV file."""
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question_id", "question", "chunks", "rationale"])
        writer.writeheader()
        for row in data:
            row["chunks"] = json.dumps(row["chunks"], ensure_ascii=False)
            writer.writerow(row)
    print(f"✅ Ground dataset CSV written to: {outpath}")


def main():
    if not os.path.exists(INPUT_JSON):
        raise FileNotFoundError(f"Missing input file: {INPUT_JSON}")

    chunks = load_chunks(INPUT_JSON)
    print(f"Loaded {len(chunks)} chunks from {INPUT_JSON} (metadata removed).")

    system_msg, user_msg = build_prompt_toon(chunks)
    raw_output = call_model(system_msg, user_msg)
    parsed = parse_json_response(raw_output)

    # Validate keys
    for entry in parsed:
        if not all(k in entry for k in ["question_id", "question", "chunks", "rationale"]):
            raise ValueError(f"Invalid entry missing required keys: {entry}")

    write_csv(parsed, OUTPUT_CSV)


if __name__ == "__main__":
    main()
