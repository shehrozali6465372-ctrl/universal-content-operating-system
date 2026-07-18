"""vector_index.py — Vector indexing."""
from __future__ import annotations
from typing import Any, Dict, List, Tuple


class VectorIndex:
    """Index for fast vector retrieval."""

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions
        self._index: Dict[int, List[float]] = {}
        self._flat: bool = True

    def add(self, record_id: int, vector: List[float]) -> None:
        self._index[record_id] = vector

    def remove(self, record_id: int) -> bool:
        return self._index.pop(record_id, None) is not None

    def search(self, query: List[float], top_k: int = 10) -> List[Tuple[int, float]]:
        results: List[Tuple[int, float]] = []
        for rid, vec in self._index.items():
            score = self._cosine(query, vec)
            results.append((rid, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return dot / (na * nb) if na > 0 and nb > 0 else 0.0

    def count(self) -> int:
        return len(self._index)

    def rebuild(self) -> bool:
        return True

    def stats(self) -> Dict[str, Any]:
        return {"vectors": len(self._index), "dimensions": self._dimensions}
