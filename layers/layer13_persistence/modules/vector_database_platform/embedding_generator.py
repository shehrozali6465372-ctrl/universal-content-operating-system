"""embedding_generator.py — Embedding generation pipeline."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.vector_database_platform.embedding_cache import EmbeddingCache
from layers.layer13_persistence.modules.vector_database_platform.embedding_manager import EmbeddingManager, EmbeddingResult


class EmbeddingGenerator:
    """Pipeline for generating embeddings with caching."""

    def __init__(self) -> None:
        self._manager = EmbeddingManager()
        self._cache = EmbeddingCache()
        self._models: Dict[str, Dict[str, Any]] = {}

    def register_model(self, name: str, dimensions: int, description: str = "") -> None:
        self._models[name] = {"dimensions": dimensions, "description": description}

    def generate(self, text: str, model: str = "default",
                 dimensions: int = 1536) -> EmbeddingResult:
        cached = self._cache.get(text, model)
        if cached:
            return EmbeddingResult(text, cached, model)
        result = self._manager.generate(text, model, dimensions)
        self._cache.set(text, result.vector, model)
        return result

    def batch_generate(self, texts: List[str], model: str = "default",
                       dimensions: int = 1536) -> List[EmbeddingResult]:
        return [self.generate(t, model, dimensions) for t in texts]

    def get_models(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._models)

    def stats(self) -> Dict[str, Any]:
        return {"manager": self._manager.stats(), "cache": self._cache.get_stats(),
                "models": len(self._models)}
