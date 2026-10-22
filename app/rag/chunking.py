"""Document chunking utility with configurable chunk size and overlap."""

import re
from typing import List, Dict, Any


def split_text_into_chunks(
    text: str,
    chunk_size_chars: int = 1500,  # ~375-500 tokens
    chunk_overlap_chars: int = 250   # ~60-80 tokens
) -> List[Dict[str, Any]]:
    """
    Recursively splits text into overlapping chunks, preserving section headers
    and paragraph boundaries wherever possible.
    """
    if not text or not text.strip():
        return []

    # Identify major section headings to tag sections
    lines = text.split("\n")
    sections: List[Dict[str, Any]] = []
    current_heading = "General Overview"
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_lines).strip()
                })
                current_lines = []
            current_heading = stripped.lstrip("#").strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "heading": current_heading,
            "content": "\n".join(current_lines).strip()
        })

    # Now create chunks from sections
    chunks: List[Dict[str, Any]] = []
    chunk_idx = 0

    for sec in sections:
        sec_text = sec["content"]
        heading = sec["heading"]
        if not sec_text:
            continue

        paragraphs = sec_text.split("\n\n")
        current_chunk_text = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk_text) + len(para) + 2 <= chunk_size_chars:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
            else:
                if current_chunk_text:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "text": current_chunk_text,
                        "heading": heading
                    })
                    chunk_idx += 1
                    # Overlap: keep the tail of the current chunk
                    overlap_text = current_chunk_text[-chunk_overlap_chars:] if len(current_chunk_text) > chunk_overlap_chars else ""
                    current_chunk_text = (overlap_text + "\n\n" + para).strip()
                else:
                    # Paragraph itself is larger than chunk_size_chars: hard-slice
                    for i in range(0, len(para), chunk_size_chars - chunk_overlap_chars):
                        sub_text = para[i:i + chunk_size_chars]
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "text": sub_text,
                            "heading": heading
                        })
                        chunk_idx += 1
                    current_chunk_text = ""

        if current_chunk_text:
            chunks.append({
                "chunk_index": chunk_idx,
                "text": current_chunk_text,
                "heading": heading
            })
            chunk_idx += 1

    return chunks
