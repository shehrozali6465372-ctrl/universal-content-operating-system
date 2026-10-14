"""hybrid_search.py — Hybrid vector + keyword search."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.shared.vector_math import cosine_similarity


class HybridSearch:
    """Combines vector similarity with keyword matching."""

    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3) -> None:
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight

    def search(self, query_vector: List[float], query_keywords: List[str],
               records: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        scored = []
        for record in records:
            vec_score = cosine_similarity(query_vector, record.get("vector", []))
            text = record.get("text", "").lower()
            kw_score = sum(1 for kw in query_keywords if kw.lower() in text) / max(1, len(query_keywords))
            combined = self._vector_weight * vec_score + self._keyword_weight * kw_score
            scored.append({**record, "score": combined})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
