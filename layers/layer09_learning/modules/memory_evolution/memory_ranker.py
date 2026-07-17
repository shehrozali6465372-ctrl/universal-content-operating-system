"""Memory Ranker — Rank memory entries by value and relevance."""
from __future__ import annotations
from typing import Any, Dict, List


class RankedMemory:
    """A memory entry with ranking metadata."""

    __slots__ = ("memory_id", "original_score", "rank", "rank_score",
                 "factors", "tier")

    def __init__(self, memory_id: str = "", original_score: float = 0.0) -> None:
        self.memory_id = memory_id
        self.original_score = original_score
        self.rank: int = 0
        self.rank_score: float = 0.0
        self.factors: Dict[str, float] = {}
        self.tier: str = "standard"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "rank": self.rank,
            "rank_score": round(self.rank_score, 3),
            "tier": self.tier,
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
        }


class MemoryRanker:
    """Rank memory entries by composite value score."""

    DEFAULT_WEIGHTS = {
        "confidence": 0.25,
        "usage": 0.25,
        "recency": 0.20,
        "quality": 0.15,
        "diversity": 0.15,
    }

    def __init__(self, weights: dict = None) -> None:
        self._weights = dict(weights or self.DEFAULT_WEIGHTS)
        self._ranked: List[RankedMemory] = []

    def rank(self, entries: List[Dict[str, Any]], top_k: int = 0) -> List[RankedMemory]:
        self._ranked.clear()
        for entry in entries:
            rm = RankedMemory(
                entry.get("entry_id", ""),
                entry.get("score", 0.0),
            )
            rm.factors = self._compute_factors(entry)
            rm.rank_score = self._weighted_score(rm.factors)
            self._ranked.append(rm)
        self._ranked.sort(key=lambda r: r.rank_score, reverse=True)
        for i, rm in enumerate(self._ranked):
            rm.rank = i + 1
            rm.tier = self._assign_tier(rm.rank, len(self._ranked))
        if top_k > 0:
            return self._ranked[:top_k]
        return list(self._ranked)

    def _compute_factors(self, entry: Dict[str, Any]) -> Dict[str, float]:
        factors = {}
        factors["confidence"] = entry.get("confidence", 0.5)
        factors["usage"] = min(1.0, entry.get("usage_count", 0) / 10.0)
        age_days = entry.get("age_days", 0.0)
        factors["recency"] = max(0.0, 1.0 - age_days / 90.0)
        factors["quality"] = entry.get("score", 0.5)
        tag_count = len(entry.get("tags", []))
        factors["diversity"] = min(1.0, tag_count / 5.0)
        return factors

    def _weighted_score(self, factors: Dict[str, float]) -> float:
        total = 0.0
        for factor, weight in self._weights.items():
            total += factors.get(factor, 0.0) * weight
        return round(total, 4)

    def _assign_tier(self, rank: int, total: int) -> str:
        if total == 0:
            return "standard"
        pct = rank / total
        if pct <= 0.1:
            return "platinum"
        elif pct <= 0.3:
            return "gold"
        elif pct <= 0.6:
            return "silver"
        return "bronze"

    def get_ranked(self) -> List[RankedMemory]:
        return list(self._ranked)

    def get_top_tier(self, tier: str = "platinum") -> List[RankedMemory]:
        return [r for r in self._ranked if r.tier == tier]
