import json
import os
from docx import Document

def extract_text_with_hierarchy(doc):
    """
    Recursively extracts text from a Word document while maintaining heading hierarchy.
    Returns a nested dictionary representing the structure.
    """
    content_tree = []
    stack = []  # track (level, section_dict)

    for para in doc.paragraphs:
        style = para.style.name if para.style else ""

        if style.startswith("Heading"):
            try:
                level = int(style.split(" ")[1])
            except:
                continue  # skip malformed headings

            section = {
                "heading": para.text.strip(),
                "level": level,
                "content": "",
                "subsections": []
            }

            # attach based on hierarchy
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


def recursive_chunk_to_flat_json(tree, parent_heading=None, parent_number=None, section_counter=[0]):
    """
    Recursively flattens nested hierarchy into a list of chunks with metadata.
    Skips empty chunks that have no content and no children.
    """
    chunks = []

    for idx, node in enumerate(tree, 1):
        # Skip completely empty nodes (no text and no subsections)
        if not node["content"].strip() and not node["subsections"]:
            continue

        section_counter[0] += 1
        section_number = f"{parent_number}.{idx}" if parent_number else str(idx)

        chunk = {
            "metadata": {
                "chunk_id": f"chunk_{section_counter[0]}",
                "section_number": section_number,
                "heading": node["heading"],
                "parent_section_number": parent_number,
                "parent_heading": parent_heading,
                "char_length": len(node["content"]),
                "word_count": len(node["content"].split())
            },
            "content": node["content"].strip()
        }

        chunks.append(chunk)

        if node["subsections"]:
            chunks.extend(
                recursive_chunk_to_flat_json(
                    node["subsections"],
                    parent_heading=node["heading"],
                    parent_number=section_number,
                    section_counter=section_counter
                )
            )

    return chunks


def recursive_chunk_docx(input_path, output_path):
    """
    Reads DOCX, performs recursive chunking, and saves structured JSON.
    """
    print(f"Processing document: {input_path}")
    doc = Document(input_path)

    hierarchy = extract_text_with_hierarchy(doc)
    chunks = recursive_chunk_to_flat_json(hierarchy)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(chunks)} non-empty chunks to {output_path}")


if __name__ == "__main__":
    input_file = "data/ACME_Enterprise_Platform (1).docx"
    output_file = "data/acme_recursive_chunks_clean.json"
    recursive_chunk_docx(input_file, output_file)
