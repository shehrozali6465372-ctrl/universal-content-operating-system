"""vector_index.py — Vector indexing."""
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math
from layers.shared.vector_math import cosine_similarity


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
            score = cosine_similarity(query, vec)
            results.append((rid, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self._index)

    def rebuild(self) -> bool:
        """Rebuild the flat index snapshot after validating stored vectors."""
        try:
            rebuilt = {
                record_id: [float(value) for value in vector]
                for record_id, vector in self._index.items()
            }
        except (TypeError, ValueError, OverflowError):
            return False
        if any(
            not math.isfinite(value)
            for vector in rebuilt.values()
            for value in vector
        ):
            return False
        dimensions = {len(vector) for vector in rebuilt.values()}
        if len(dimensions) > 1:
            return False
        if dimensions:
            self._dimensions = dimensions.pop()
        self._index = rebuilt
        self._flat = True
        return True

    def stats(self) -> Dict[str, Any]:
        return {"vectors": len(self._index), "dimensions": self._dimensions}
