"""API router for knowledge base inspection, ingestion, and direct RAG search."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.rag.retriever import ChromaKnowledgeRetriever
from app.rag.citations import format_sources_for_ui

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
retriever = ChromaKnowledgeRetriever()


class KnowledgeQueryRequest(BaseModel):
    query: str
    topic: Optional[str] = None
    top_k: int = 5


@router.get("/sources")
def get_knowledge_sources():
    """Lists all distinct source documents currently indexed in ChromaDB."""
    sources = retriever.get_indexed_sources()
    return {
        "total_documents": len(sources),
        "total_chunks": retriever.collection.count(),
        "sources": sources
    }


@router.post("/query")
def query_knowledge_base(req: KnowledgeQueryRequest):
    """Executes a semantic vector query against the knowledge base."""
    results = retriever.retrieve(req.query, topic=req.topic, top_k=req.top_k)
    return {
        "query": req.query,
        "topic": req.topic,
        "results_count": len(results),
        "passages": results,
        "formatted_citations": format_sources_for_ui(results)
    }


@router.post("/ingest")
def trigger_knowledge_ingestion(kb_dir: str = "./knowledge_base"):
    """Triggers idempotent ingestion of local knowledge base directory."""
    try:
        stats = retriever.ingest_directory(kb_dir)
        return {
            "status": "success",
            "files_ingested": stats["files_ingested"],
            "total_chunks": stats["total_chunks"],
            "details": stats["details"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
