import json
import os
from docx import Document

def extract_text_with_hierarchy(doc):
    """
    Extract text from DOCX with heading hierarchy.
    Returns a nested dictionary representing structure.
    """
    content_tree = []
    stack = []

    for para in doc.paragraphs:
        style = para.style.name if para.style else ""

        if style.startswith("Heading"):
            try:
                level = int(style.split(" ")[1])
            except:
                continue

            section = {
                "heading": para.text.strip(),
                "level": level,
                "content": "",
                "subsections": []
            }

            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                content_tree.append(section)
            else:
                stack[-1][1]["subsections"].append(section)

            stack.append((level, section))
        else:
            text = para.text.strip()
            if not text:
                continue
            if stack:
                stack[-1][1]["content"] += text + "\n"

    return content_tree


def split_text_recursive(text, max_chars=500, overlap=50):
    """
    Split text into character-based chunks with overlap.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + max_chars, text_length)
        chunk_text = text[start:end]
        chunks.append(chunk_text)
        start += max_chars - overlap  # move forward with overlap

    return chunks


def recursive_chunk_to_flat_json(tree, parent_heading=None, parent_number=None, section_counter=[0],
                                 max_chars=500, overlap=50):
    """
    Flatten hierarchy into chunks with recursive character splitting.
    """
    chunks = []

    for idx, node in enumerate(tree, 1):
        # Skip completely empty nodes
        if not node["content"].strip() and not node["subsections"]:
            continue

        section_number = f"{parent_number}.{idx}" if parent_number else str(idx)

        # Split the content into smaller chunks
        content_chunks = split_text_recursive(node["content"], max_chars=max_chars, overlap=overlap)
        for c_idx, chunk_text in enumerate(content_chunks, 1):
            section_counter[0] += 1
            chunk = {
                "metadata": {
                    "chunk_id": f"chunk_{section_counter[0]}",
                    "section_number": section_number,
                    "subchunk_number": c_idx,
                    "heading": node["heading"],
                    "parent_section_number": parent_number,
                    "parent_heading": parent_heading,
                    "char_length": len(chunk_text),
                    "word_count": len(chunk_text.split())
                },
                "content": chunk_text.strip()
            }
            chunks.append(chunk)

        # Recursively process subsections
        if node["subsections"]:
            chunks.extend(
                recursive_chunk_to_flat_json(
                    node["subsections"],
                    parent_heading=node["heading"],
                    parent_number=section_number,
                    section_counter=section_counter,
                    max_chars=max_chars,
                    overlap=overlap
                )
            )

    return chunks


def recursive_chunk_docx(input_path, output_path, max_chars=500, overlap=50):
    """
    Reads DOCX, performs recursive character chunking, and saves JSON.
    """
    print(f"Processing document: {input_path}")
    doc = Document(input_path)

    hierarchy = extract_text_with_hierarchy(doc)
    chunks = recursive_chunk_to_flat_json(hierarchy, max_chars=max_chars, overlap=overlap)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    input_file = "data/ACME_Enterprise_Platform (1).docx"
    output_file = "data/acme_recursive_chunks_char.json"
    recursive_chunk_docx(input_file, output_file, max_chars=500, overlap=50)
