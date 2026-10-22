"""Document ingestion utility supporting TXT, MD, PDF, and DOCX."""

import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.rag.chunking import split_text_into_chunks


def extract_text_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extracts text from a given file path.
    Returns a list of page/section items with page numbers where applicable.
    Format: [{"page": Optional[int], "text": str}]
    """
    ext = file_path.suffix.lower()

    if ext in (".txt", ".md", ".markdown"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return [{"page": 1, "text": f.read()}]

    elif ext == ".pdf":
        pages = []
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"page": i + 1, "text": text})
            return pages
        except Exception:
            # Fallback to pymupdf if available
            try:
                import fitz
                doc = fitz.open(str(file_path))
                for i, page in enumerate(doc):
                    text = page.get_text() or ""
                    if text.strip():
                        pages.append({"page": i + 1, "text": text})
                return pages
            except Exception as e:
                raise RuntimeError(f"Failed to parse PDF file '{file_path}': {e}")

    elif ext in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(str(file_path))
            full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return [{"page": 1, "text": full_text}]
        except Exception as e:
            raise RuntimeError(f"Failed to parse DOCX file '{file_path}': {e}")

    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported formats: .txt, .md, .pdf, .docx")


def ingest_document(
    file_path: Path,
    topic: Optional[str] = None,
    chunk_size_chars: int = 1500,
    chunk_overlap_chars: int = 250
) -> List[Dict[str, Any]]:
    """
    Parses, chunks, and attaches metadata to a document.
    Returns idempotent chunks ready for vector indexing.
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine topic from parent directory if not provided
    if not topic:
        parent_dir = path_obj.parent.name
        topic = parent_dir if parent_dir not in ("knowledge_base", "data", "schedulai") else "general"

    doc_id = path_obj.stem
    doc_title = doc_id.replace("_", " ").title()

    extracted_pages = extract_text_from_file(path_obj)
    all_chunks: List[Dict[str, Any]] = []

    global_chunk_counter = 0
    for page_data in extracted_pages:
        page_num = page_data.get("page", 1)
        page_text = page_data.get("text", "")
        
        # Split text into overlapping chunks
        raw_chunks = split_text_into_chunks(
            page_text,
            chunk_size_chars=chunk_size_chars,
            chunk_overlap_chars=chunk_overlap_chars
        )

        for chunk in raw_chunks:
            chunk_id = f"{doc_id}_p{page_num}_c{global_chunk_counter}"
            all_chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "document_title": doc_title,
                "source_filename": path_obj.name,
                "page_number": page_num,
                "section_heading": chunk.get("heading", "General"),
                "topic": topic,
                "text": chunk.get("text", "")
            })
            global_chunk_counter += 1

    return all_chunks
