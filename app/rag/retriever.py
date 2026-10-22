"""Vector storage and retrieval pipeline using ChromaDB."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.rag.embeddings import EmbeddingGenerator
from app.rag.ingestion import ingest_document


class ChromaKnowledgeRetriever:
    """
    Manages persistent vector indexing and semantic retrieval in ChromaDB.
    """
    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "schedulai_kb",
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedding_generator or EmbeddingGenerator()

        # Initialize Chroma persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "SchedulAI CPU Process Scheduling Knowledge Base"}
        )

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Idempotently inserts or updates chunks in ChromaDB.
        """
        if not chunks:
            return 0

        chunk_ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": c.get("document_id", "doc"),
                "document_title": c.get("document_title", "Title"),
                "source_filename": c.get("source_filename", "file.txt"),
                "page_number": int(c.get("page_number", 1)),
                "section_heading": c.get("section_heading", "General"),
                "topic": c.get("topic", "general")
            }
            for c in chunks
        ]

        embeddings = self.embedder.embed_texts(texts)

        # Batch upsert into Chroma
        batch_size = 100
        total_upserted = 0
        for i in range(0, len(chunks), batch_size):
            b_ids = chunk_ids[i:i + batch_size]
            b_texts = texts[i:i + batch_size]
            b_meta = metadatas[i:i + batch_size]
            b_emb = embeddings[i:i + batch_size]

            self.collection.upsert(
                ids=b_ids,
                documents=b_texts,
                metadatas=b_meta,
                embeddings=b_emb
            )
            total_upserted += len(b_ids)

        return total_upserted

    def ingest_directory(
        self,
        directory_path: str,
        chunk_size_chars: int = 1500,
        chunk_overlap_chars: int = 250
    ) -> Dict[str, Any]:
        """
        Recursively scans a directory, chunks all supported files, and indexes them.
        """
        dir_path = Path(directory_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        supported_exts = {".txt", ".md", ".markdown", ".pdf", ".docx"}
        ingested_files = []
        total_chunks = 0

        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                try:
                    chunks = ingest_document(
                        file_path=file_path,
                        chunk_size_chars=chunk_size_chars,
                        chunk_overlap_chars=chunk_overlap_chars
                    )
                    if chunks:
                        upserted = self.upsert_chunks(chunks)
                        total_chunks += upserted
                        ingested_files.append({
                            "filename": file_path.name,
                            "path": str(file_path),
                            "chunks": len(chunks)
                        })
                except Exception as e:
                    print(f"Error ingesting file {file_path}: {e}")

        return {
            "files_ingested": len(ingested_files),
            "total_chunks": total_chunks,
            "details": ingested_files
        }

    def retrieve(
        self,
        query: str,
        topic: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search for a query with optional topic filtering.
        """
        if not query or not query.strip():
            return []

        count = self.collection.count()
        if count == 0:
            return []

        k = min(top_k, count)
        query_emb = self.embedder.embed_query(query)

        where_clause = None
        if topic and topic.strip() and topic.lower() not in ("all", "general", "scheduling"):
            where_clause = {"topic": topic.strip().lower()}

        try:
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=k,
                where=where_clause
            )
        except Exception:
            # If where-clause yields no match or fails, fallback to unconstrained query
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=k
            )

        passages: List[Dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            # Fallback to general query if topic-filtered returned nothing
            if where_clause:
                results = self.collection.query(query_embeddings=[query_emb], n_results=k)

        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

            for cid, doc, meta, dist in zip(ids, docs, metas, distances):
                passages.append({
                    "chunk_id": cid,
                    "text": doc,
                    "metadata": meta,
                    "distance": float(dist)
                })

        return passages

    def get_indexed_sources(self) -> List[Dict[str, Any]]:
        """Returns metadata summaries for all distinct ingested documents."""
        count = self.collection.count()
        if count == 0:
            return []

        # Fetch all metadata
        all_data = self.collection.get(include=["metadatas"])
        docs_map: Dict[str, Dict[str, Any]] = {}

        if all_data and all_data.get("metadatas"):
            for meta in all_data["metadatas"]:
                doc_id = meta.get("document_id", "unknown")
                if doc_id not in docs_map:
                    docs_map[doc_id] = {
                        "document_id": doc_id,
                        "document_title": meta.get("document_title", "Unknown"),
                        "source_filename": meta.get("source_filename", ""),
                        "topic": meta.get("topic", "general"),
                        "chunk_count": 0
                    }
                docs_map[doc_id]["chunk_count"] += 1

        return list(docs_map.values())
