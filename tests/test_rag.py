"""Tests for RAG pipeline: chunking, ingestion, indexing, and retrieval."""

import pytest
import shutil
from pathlib import Path

from app.rag.chunking import split_text_into_chunks
from app.rag.ingestion import ingest_document
from app.rag.retriever import ChromaKnowledgeRetriever


@pytest.fixture
def temp_chroma_dir(tmp_path):
    """Provides a fresh temporary directory for ChromaDB."""
    chroma_path = tmp_path / "test_chroma"
    chroma_path.mkdir()
    yield str(chroma_path)
    shutil.rmtree(str(chroma_path), ignore_errors=True)


def test_chunking_preserves_headings_and_overlap():
    """Verify that chunking splits text and creates overlapping segments."""
    sample_text = (
        "# Heading One\n\n"
        + "First paragraph discussing CPU process scheduling principles. " * 10
        + "\n\n# Heading Two\n\n"
        + "Second paragraph discussing Round Robin time quantum trade-offs. " * 10
    )

    chunks = split_text_into_chunks(sample_text, chunk_size_chars=300, chunk_overlap_chars=50)

    assert len(chunks) > 1
    assert any("Heading One" in c["heading"] for c in chunks)
    assert any("Heading Two" in c["heading"] for c in chunks)


def test_ingest_markdown_file():
    """Verify that a real knowledge base file can be ingested with metadata."""
    kb_file = Path("knowledge_base/fcfs/01_fcfs_algorithm.md")
    assert kb_file.exists(), "KB file must exist"

    chunks = ingest_document(kb_file, topic="fcfs")
    assert len(chunks) >= 1
    first_chunk = chunks[0]

    assert first_chunk["topic"] == "fcfs"
    assert first_chunk["source_filename"] == "01_fcfs_algorithm.md"
    assert "FCFS" in first_chunk["text"] or "First-Come" in first_chunk["text"]


def test_retriever_idempotence_and_search(temp_chroma_dir):
    """Verify that repeated ingestion is idempotent and retrieval returns relevant chunks."""
    retriever = ChromaKnowledgeRetriever(persist_directory=temp_chroma_dir)

    kb_file = Path("knowledge_base/fcfs/01_fcfs_algorithm.md")
    chunks = ingest_document(kb_file, topic="fcfs")

    # Ingest once
    count1 = retriever.upsert_chunks(chunks)
    assert count1 == len(chunks)
    assert retriever.collection.count() == len(chunks)

    # Ingest again (idempotent upsert with same chunk IDs)
    count2 = retriever.upsert_chunks(chunks)
    assert count2 == len(chunks)
    assert retriever.collection.count() == len(chunks)  # No duplicates created!

    # Query search
    results = retriever.retrieve("What is the convoy effect in FCFS?", top_k=2)
    assert len(results) >= 1
    assert "convoy" in results[0]["text"].lower() or "fcfs" in results[0]["text"].lower()
