"""
Memory Ranker
Layer 2: Research Engine — Module 7

Ranks research entries by multiple factors:
- Recency
- Credibility
- Relevance
- Access frequency
- Composite scoring
"""

from typing import Dict, List, Optional


class MemoryRanker:
    """Rank research entries by configurable weights."""

    DEFAULT_WEIGHTS = {
        "credibility": 0.30,
        "relevance": 0.30,
        "freshness": 0.20,
        "access_frequency": 0.10,
        "composite": 0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._weights = weights or dict(self.DEFAULT_WEIGHTS)

    def rank(self, entries: List[dict], max_results: int = 20) -> List[dict]:
        """Rank entries by weighted score."""
        scored = []
        for entry in entries:
            score = self._compute_score(entry)
            scored.append({**entry, "_rank_score": score})
        scored.sort(key=lambda e: e["_rank_score"], reverse=True)
        return scored[:max_results]

    def _compute_score(self, entry: dict) -> float:
        """Compute weighted score for an entry."""
        cred = entry.get("credibility_score", 0.5)
        rel = entry.get("relevance_score", 0.5)
        fresh = entry.get("freshness_score", 0.5)
        access = min(1.0, entry.get("access_count", 0) / 100)
        comp = entry.get("composite_score", 0.5)

        score = (
            cred * self._weights.get("credibility", 0.3) +
            rel * self._weights.get("relevance", 0.3) +
            fresh * self._weights.get("freshness", 0.2) +
            access * self._weights.get("access_frequency", 0.1) +
            comp * self._weights.get("composite", 0.1)
        )
        return round(score, 4)

    def rank_by_field(self, entries: List[dict], field: str, descending: bool = True) -> List[dict]:
        """Rank by a single field."""
        return sorted(entries, key=lambda e: e.get(field, 0), reverse=descending)

    def filter_above_threshold(self, entries: List[dict], min_score: float = 0.5) -> List[dict]:
        """Filter entries above a minimum composite score."""
        return [e for e in entries if self._compute_score(e) >= min_score]
