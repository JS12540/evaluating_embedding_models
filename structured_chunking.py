import json
import os
from docx import Document

INPUT_DOCX = "data/ACME_Enterprise_Platform (1).docx"
OUTPUT_JSON = "data/chunks.json"
os.makedirs("data", exist_ok=True)

# Define TOC structure from the document
STRUCTURE = {
    "1": {"heading": "Executive Summary", "subsections": []},
    "2": {
        "heading": "Introduction to Acme",
        "subsections": [
            {"number": "2.1", "heading": "Our Mission"},
            {"number": "2.2", "heading": "The Acme Platform: Redefining Enterprise Communication"}
        ]
    },
    "3": {
        "heading": "Core Platform Features",
        "subsections": [
            {"number": "3.1", "heading": "Seamless Communication"},
            {"number": "3.2", "heading": "Enhanced Collaboration"},
            {"number": "3.3", "heading": "Productivity & Workflow Automation"}
        ]
    },
    "4": {
        "heading": "Acme Intelligence: The Future of Work",
        "subsections": [
            {"number": "4.1", "heading": "AI-Powered Summaries & Recaps"},
            {"number": "4.2", "heading": "Intelligent Search & Discovery"},
            {"number": "4.3", "heading": "Proactive Task & Action Item Detection"},
            {"number": "4.4", "heading": "AI and Data Governance"}
        ]
    },
    "5": {
        "heading": "Enterprise-Grade Security",
        "subsections": [
            {"number": "5.1", "heading": "Data Encryption"},
            {"number": "5.2", "heading": "Identity and Access Management (IAM)"},
            {"number": "5.3", "heading": "Network and Infrastructure Security"},
            {"number": "5.4", "heading": "Application Security & DevSecOps"},
            {"number": "5.5", "heading": "Physical Security of Data Centers"}
        ]
    },
    "6": {
        "heading": "Compliance and Data Governance",
        "subsections": [
            {"number": "6.1", "heading": "Global Certifications and Attestations"},
            {"number": "6.2", "heading": "Data Residency and Sovereignty"},
            {"number": "6.3", "heading": "eDiscovery & Legal Hold"},
            {"number": "6.4", "heading": "Data Loss Prevention (DLP)"}
        ]
    },
    "7": {
        "heading": "Reliability & Disaster Recovery",
        "subsections": [
            {"number": "7.1", "heading": "High-Availability Architecture"},
            {"number": "7.2", "heading": "Backup and Recovery Strategy"},
            {"number": "7.3", "heading": "Disaster Recovery (DR) Plan and Testing"}
        ]
    },
    "8": {
        "heading": "Platform Architecture & Integrations",
        "subsections": [
            {"number": "8.1", "heading": "High-Level System Architecture"},
            {"number": "8.2", "heading": "Robust API and Integration Ecosystem"}
        ]
    },
    "9": {
        "heading": "Company Overview & Structure",
        "subsections": [
            {"number": "9.1", "heading": "Leadership Team"},
            {"number": "9.2", "heading": "Organizational Commitment to Security"},
            {"number": "9.3", "heading": "Our Enterprise Focus"}
        ]
    },
    "10": {"heading": "Support & Professional Services", "subsections": []},
    "11": {"heading": "Contact Information", "subsections": []},
    "12": {
        "heading": "Advanced Security & Threat Management",
        "subsections": [
            {"number": "12.1", "heading": "Zero Trust Architecture Philosophy"},
            {"number": "12.2", "heading": "Proactive Threat Intelligence Program"},
            {"number": "12.3", "heading": "Incident Response Lifecycle"},
            {"number": "12.4", "heading": "Software Supply Chain Security (SBOM)"}
        ]
    },
    "13": {
        "heading": "Advanced Data Governance & Control",
        "subsections": [
            {"number": "13.1", "heading": "Customizable Data Retention Policies"},
            {"number": "13.2", "heading": "Ethical Walls & Information Barriers"},
            {"number": "13.3", "heading": "Comprehensive Audit Logs for SIEM Integration"}
        ]
    },
    "14": {
        "heading": "Responsible AI & Model Governance",
        "subsections": [
            {"number": "14.1", "heading": "Acme's AI Ethics Framework"},
            {"number": "14.2", "heading": "AI Model Governance and Validation"}
        ]
    },
    "15": {
        "heading": "Mobile Enterprise Management",
        "subsections": [
            {"number": "15.1", "heading": "MDM & MAM Integration"},
            {"number": "15.2", "heading": "Mobile-Specific Security Controls"}
        ]
    },
    "16": {
        "heading": "Platform Scalability & Accessibility",
        "subsections": [
            {"number": "16.1", "heading": "Proven Scalability Metrics"},
            {"number": "16.2", "heading": "Global Performance Architecture"},
            {"number": "16.3", "heading": "Commitment to Accessibility (WCAG 2.1)"}
        ]
    },
    "17": {
        "heading": "Enterprise Partnership & Success",
        "subsections": [
            {"number": "17.1", "heading": "Change Management & Adoption Services"},
            {"number": "17.2", "heading": "Enterprise Customer Advisory Board (CAB)"},
            {"number": "17.3", "heading": "Service Level Agreement (SLA) Breakdown"}
        ]
    }
}



def build_sections_to_chunk():
    """
    Build a flat list of sections to chunk based on TOC structure.
    Rule: If section has subsections, only chunk the subsections.
          If section has no subsections, chunk the main section.
    """
    sections = []
    
    for num, data in STRUCTURE.items():
        if data["subsections"]:
            # Has subsections - only add subsections
            for sub in data["subsections"]:
                sections.append({
                    "section_number": sub["number"],
                    "heading": sub["heading"],
                    "parent_section": num,
                    "parent_heading": data["heading"]
                })
        else:
            # No subsections - add the main section
            sections.append({
                "section_number": num,
                "heading": data["heading"],
                "parent_section": None,
                "parent_heading": None
            })
    
    return sections


def get_content_paragraphs(doc):
    """
    Get all paragraphs starting from page 3 (content after TOC).
    """
    paragraphs = []
    found_start = False
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        # Start from "1. Executive Summary"
        if not found_start and text.startswith("1.") and "Executive Summary" in text:
            found_start = True
        
        if found_start:
            paragraphs.append(text)
    
    return paragraphs


def find_section_index(section_num, heading, paragraphs):
    """
    Find the paragraph index where this section starts.
    """
    # Try different matching patterns
    patterns = [
        f"{section_num}. {heading}",
        f"{section_num}.  {heading}",
        f"{section_num} {heading}"
    ]
    
    for i, para in enumerate(paragraphs):
        for pattern in patterns:
            if para.startswith(pattern):
                return i
    
    return None


def chunk_document(docx_path):
    """
    Main chunking logic.
    """
    print("="*80)
    print("ACME Document Chunking")
    print("="*80)
    print()
    
    # Load document
    print(f"Loading document: {docx_path}")
    doc = Document(docx_path)
    
    # Build sections list from TOC
    print("\nStep 1: Building sections to chunk from TOC structure...")
    sections_to_chunk = build_sections_to_chunk()
    print(f"Total sections to chunk: {len(sections_to_chunk)}")
    print("-"*80)
    for sec in sections_to_chunk:
        parent_info = f" (parent: {sec['parent_section']})" if sec['parent_section'] else ""
        print(f"  {sec['section_number']:<10} | {sec['heading']}{parent_info}")
    print("-"*80)
    
    # Get all content paragraphs
    print("\nStep 2: Extracting content paragraphs from page 3...")
    paragraphs = get_content_paragraphs(doc)
    print(f"Extracted {len(paragraphs)} paragraphs")
    
    # Find each section in the content
    print("\nStep 3: Locating sections in content...")
    section_positions = []
    
    for sec in sections_to_chunk:
        idx = find_section_index(sec["section_number"], sec["heading"], paragraphs)
        if idx is not None:
            section_positions.append({
                **sec,
                "para_index": idx
            })
            print(f"  ✓ Found {sec['section_number']:<10} at paragraph {idx}")
        else:
            print(f"  ✗ NOT FOUND: {sec['section_number']} - {sec['heading']}")
    
    # Create chunks
    print(f"\nStep 4: Creating chunks from {len(section_positions)} sections...")
    chunks = []
    
    for i, section in enumerate(section_positions):
        # Content starts after the heading paragraph
        start_idx = section["para_index"] + 1
        
        # Content ends at the next section heading (or end of document)
        if i + 1 < len(section_positions):
            end_idx = section_positions[i + 1]["para_index"]
        else:
            end_idx = len(paragraphs)
        
        # Extract content paragraphs
        content_paras = paragraphs[start_idx:end_idx]
        content = "\n".join(content_paras).strip()
        
        if not content:
            print(f"  ⚠ Warning: No content for {section['section_number']}")
            continue
        
        # Build metadata
        metadata = {
            "chunk_id": f"acme_{section['section_number']}",
            "section_number": section["section_number"],
            "heading": section["heading"],
            "parent_section_number": section["parent_section"],
            "parent_heading": section["parent_heading"],
            "char_length": len(content),
            "word_count": len(content.split())
        }
        
        chunks.append({
            "metadata": metadata,
            "content": content
        })
        
        print(f"  ✓ Chunk {section['section_number']:<10} - {metadata['word_count']:>6} words")
    
    # Sort chunks by section number
    def sort_key(c):
        parts = c["metadata"]["section_number"].split(".")
        return [int(x) for x in parts]
    
    chunks.sort(key=sort_key)
    
    print(f"\nTotal chunks created: {len(chunks)}")
    return chunks


if __name__ == "__main__":
    chunks = chunk_document(INPUT_DOCX)
    
    # Save to JSON
    print(f"\nSaving to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully saved {len(chunks)} chunks\n")
    
    # Print summary table
    print("="*80)
    print("CHUNK SUMMARY")
    print("="*80)
    print(f"{'Section':<12} | {'Words':<8} | {'Parent':<8} | {'Heading'}")
    print("-"*80)
    for chunk in chunks:
        meta = chunk["metadata"]
        parent = meta["parent_section_number"] or "-"
        indent = "  " if meta["parent_section_number"] else ""
        print(f"{meta['section_number']:<12} | {meta['word_count']:<8} | {parent:<8} | {indent}{meta['heading']}")
    print("="*80)