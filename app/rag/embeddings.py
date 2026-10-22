"""Embedding generation for RAG document chunking and queries."""

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["ORT_LOGGING_LEVEL"] = "3"
import numpy as np
from typing import List, Optional


class EmbeddingGenerator:
    """
    Manages embedding model loading and inference.
    Uses ChromaDB's ONNX-based all-MiniLM-L6-v2 embedding model by default,
    with sentence-transformers and hashing fallbacks.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._ef = None

    def _get_ef(self):
        if self._ef is None:
            try:
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                self._ef = DefaultEmbeddingFunction()
            except Exception as e:
                print(f"[EmbeddingGenerator] Could not load DefaultEmbeddingFunction: {e}")
                self._ef = None
        return self._ef

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of texts."""
        if not texts:
            return []

        ef = self._get_ef()
        if ef is not None:
            try:
                embeddings = ef(texts)
                # Convert to standard Python float primitives to ensure compatibility with Chroma's type checks
                return [[float(val) for val in row] for row in embeddings]
            except Exception as e:
                print(f"[EmbeddingGenerator] DefaultEmbeddingFunction error: {e}")

        # Fallback to deterministic pseudo-dense embeddings via hashing
        return self._fallback_embed(texts)

    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a single search query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * 384

    def _fallback_embed(self, texts: List[str], dim: int = 384) -> List[List[float]]:
        """Deterministic 384-dimensional hashed word-vector representation."""
        results = []
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            words = text.lower().split()
            for w in words:
                idx = hash(w) % dim
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 1e-6:
                vec = vec / norm
            results.append(vec.tolist())
        return results
