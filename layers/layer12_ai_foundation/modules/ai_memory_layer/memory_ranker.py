"""MemoryRanker — rank memories by relevance, importance, and recency."""
from __future__ import annotations

from typing import Dict, List, Optional

from .models import MemoryEntry


class MemoryRanker:
    """Rank memories by relevance, importance, and recency."""

    def __init__(self) -> None:
        self._weights: Dict[str, float] = {
            "relevance": 0.4, "importance": 0.3, "recency": 0.2, "access_count": 0.1,
        }

    def rank(self, entries: List[MemoryEntry], query: str = "",
             weights: Optional[Dict[str, float]] = None) -> List[MemoryEntry]:
        weights = weights or self._weights
        import time
        now = time.time()

        query_words = set(query.lower().split()) if query else set()
        scored: List[tuple] = []
        for e in entries:
            score = 0.0
            # Relevance
            if query_words:
                content_words = set(e.content.lower().split())
                relevance = len(query_words & content_words) / max(len(query_words), 1)
            else:
                relevance = 0.5
            score += relevance * weights.get("relevance", 0.4)
            score += e.importance * weights.get("importance", 0.3)
            # Recency (normalize to 0-1, more recent = higher)
            age_hours = (now - e.last_accessed) / 3600
            recency = max(0.0, 1.0 - min(age_hours / 168, 1.0))  # 1 week half
            score += recency * weights.get("recency", 0.2)
            # Access count
            access_score = min(e.access_count / 10, 1.0)
            score += access_score * weights.get("access_count", 0.1)
            scored.append((e, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored]

    def get_top(self, entries: List[MemoryEntry], top_n: int = 5,
                query: str = "") -> List[MemoryEntry]:
        return self.rank(entries, query)[:top_n]
