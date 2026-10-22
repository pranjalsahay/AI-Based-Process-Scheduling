"""Health check endpoint verifying Ollama, ChromaDB, SQLite, and system resources."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.connection import get_db
from app.config import settings, inspect_hardware_resources
from app.core.llm_client import OllamaClient
from app.rag.retriever import ChromaKnowledgeRetriever

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def check_health(db: Session = Depends(get_db)):
    """Comprehensive health check for backend services."""
    # 1. Database check
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_err = str(e)

    # 2. Ollama & LLM check
    ollama_client = OllamaClient()
    available_models = await ollama_client.get_available_models()
    active_model = await ollama_client.select_model()
    ollama_ok = len(available_models) > 0

    # 3. ChromaDB check
    chroma_ok = False
    doc_count = 0
    try:
        retriever = ChromaKnowledgeRetriever()
        doc_count = retriever.collection.count()
        chroma_ok = True
    except Exception:
        pass

    # 4. Hardware resources
    hardware = inspect_hardware_resources()

    overall_status = "healthy" if (db_ok and chroma_ok) else "degraded"
    if not ollama_ok:
        llm_status = "offline_fallback_active"
    else:
        llm_status = "ready"

    return {
        "status": overall_status,
        "services": {
            "database": {"status": "up" if db_ok else "down"},
            "ollama_llm": {
                "status": llm_status,
                "preferred_model": settings.OLLAMA_MODEL,
                "active_model": active_model,
                "available_models": available_models
            },
            "vector_store_chromadb": {
                "status": "up" if chroma_ok else "down",
                "indexed_chunks": doc_count
            }
        },
        "hardware": hardware,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }
