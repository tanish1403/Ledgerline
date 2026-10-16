"""Embedder interface supporting sentence-transformers (bge-small) and fallback test mode."""

import os
from typing import List
import numpy as np


class Embedder:
    """Embedding provider with sentence-transformers default (BAAI/bge-small-en-v1.5)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                # Fallback to deterministic random projection for tests / offline environments without internet
                self._model = "fake"

    def embed(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        if self._model == "fake":
            # Deterministic pseudo-embeddings for unit tests
            embeddings = []
            for t in texts:
                np.random.seed(abs(hash(t)) % (2**32))
                vec = np.random.randn(self.dim).astype(float)
                vec /= np.linalg.norm(vec) + 1e-9
                embeddings.append(vec.tolist())
            return embeddings

        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()


embedder = Embedder()
