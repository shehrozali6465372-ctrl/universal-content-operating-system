"""embedding_manager.py — Embedding generation and management."""
from __future__ import annotations
import hashlib
import time
from typing import Any, Dict, List, Optional


class EmbeddingResult:
    """Result of an embedding operation."""
    __slots__ = ("embedding_id", "text", "vector", "model", "dimensions",
                 "metadata", "created_at")
    _counter = 0

    def __init__(self, text: str, vector: List[float], model: str = "default") -> None:
        EmbeddingResult._counter += 1
        self.embedding_id: int = EmbeddingResult._counter
        self.text = text
        self.vector = vector
        self.model = model
        self.dimensions = len(vector)
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.embedding_id, "text": self.text[:200],
                "dimensions": self.dimensions, "model": self.model}


class EmbeddingManager:
    """Manages vector embeddings."""

    def __init__(self) -> None:
        self._embeddings: Dict[int, EmbeddingResult] = {}
        self._cache: Dict[str, int] = {}

    def generate(self, text: str, model: str = "default",
                 dimensions: int = 1536) -> EmbeddingResult:
        cache_key = hashlib.md5(f"{model}:{text}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._embeddings[self._cache[cache_key]]
        h = hashlib.md5(text.encode()).hexdigest()
        vector = [float(int(h[i:i + 2], 16)) / 255.0 for i in range(0, min(32, len(h)), 2)]
        while len(vector) < dimensions:
            vector.append(0.0)
        vector = vector[:dimensions]
        result = EmbeddingResult(text, vector, model)
        self._embeddings[result.embedding_id] = result
        self._cache[cache_key] = result.embedding_id
        return result

    def batch_generate(self, texts: List[str], model: str = "default",
                       dimensions: int = 1536) -> List[EmbeddingResult]:
        return [self.generate(t, model, dimensions) for t in texts]

    def get(self, embedding_id: int) -> Optional[EmbeddingResult]:
        return self._embeddings.get(embedding_id)

    def delete(self, embedding_id: int) -> bool:
        return self._embeddings.pop(embedding_id, None) is not None

    def count(self) -> int:
        return len(self._embeddings)

    def similarity(self, a: EmbeddingResult, b: EmbeddingResult) -> float:
        if a.dimensions != b.dimensions or a.dimensions == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a.vector, b.vector))
        norm_a = sum(x * x for x in a.vector) ** 0.5
        norm_b = sum(x * x for x in b.vector) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def stats(self) -> Dict[str, Any]:
        return {"embeddings": len(self._embeddings), "cached": len(self._cache)}
