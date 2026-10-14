"""similarity_search.py — Similarity search engine."""
from __future__ import annotations
from typing import List, Tuple
from layers.shared.vector_math import cosine_similarity, dot_product


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
            return cosine_similarity(a, b)
        elif self._metric == "euclidean":
            return self._euclidean(a, b)
        elif self._metric == "dot":
            return dot_product(a, b)
        return cosine_similarity(a, b)

    def _euclidean(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dist = sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
        return 1.0 / (1.0 + dist)

    def batch_search(self, queries: List[List[float]], vectors: List[Tuple[int, List[float]]],
                     top_k: int = 10) -> List[List[Tuple[int, float]]]:
        return [self.search(q, vectors, top_k) for q in queries]
