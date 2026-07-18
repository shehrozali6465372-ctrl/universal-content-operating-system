"""similarity_search.py — Similarity search engine."""
from __future__ import annotations
from typing import List, Tuple


class SimilaritySearch:
    """Advanced similarity search with multiple distance metrics."""

    def __init__(self) -> None:
        self._metric: str = "cosine"

    def set_metric(self, metric: str) -> None:
        self._metric = metric

    def search(self, query: List[float], vectors: List[Tuple[int, List[float]]],
               top_k: int = 10) -> List[Tuple[int, float]]:
        results: List[Tuple[int, float]] = []
        for vid, vec in vectors:
            score = self._compute(query, vec)
            results.append((vid, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _compute(self, a: List[float], b: List[float]) -> float:
        if self._metric == "cosine":
            return self._cosine(a, b)
        elif self._metric == "euclidean":
            return self._euclidean(a, b)
        elif self._metric == "dot":
            return self._dot(a, b)
        return self._cosine(a, b)

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return dot / (na * nb) if na > 0 and nb > 0 else 0.0

    def _euclidean(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dist = sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
        return 1.0 / (1.0 + dist)

    def _dot(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))

    def batch_search(self, queries: List[List[float]], vectors: List[Tuple[int, List[float]]],
                     top_k: int = 10) -> List[List[Tuple[int, float]]]:
        return [self.search(q, vectors, top_k) for q in queries]
