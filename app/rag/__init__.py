"""RAG package initialization."""

from app.rag.chunking import split_text_into_chunks
from app.rag.ingestion import ingest_document, extract_text_from_file
from app.rag.embeddings import EmbeddingGenerator
from app.rag.retriever import ChromaKnowledgeRetriever
from app.rag.citations import Citation, format_passages_for_prompt, format_sources_for_ui

__all__ = [
    "split_text_into_chunks",
    "ingest_document",
    "extract_text_from_file",
    "EmbeddingGenerator",
    "ChromaKnowledgeRetriever",
    "Citation",
    "format_passages_for_prompt",
    "format_sources_for_ui"
]
