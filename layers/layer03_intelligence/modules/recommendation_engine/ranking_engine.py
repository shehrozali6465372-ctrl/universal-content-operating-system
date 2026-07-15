"""Ranking Engine - Ranks candidates using weighted multi-signal scoring."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RankedCandidate:
    """A ranked candidate with final score."""
    __slots__ = ("topic", "final_score", "rank", "signal_scores", "source")

    def __init__(self, topic: str = "", final_score: float = 0.0, rank: int = 0):
        self.topic = topic
        self.final_score = final_score
        self.rank = rank
        self.signal_scores: Dict[str, float] = {}
        self.source = ""

    def to_dict(self) -> Dict:
        return {"topic": self.topic, "final_score": round(self.final_score, 3),
                "rank": self.rank, "source": self.source,
                "signal_scores": {k: round(v, 3) for k, v in self.signal_scores.items()}}


class RankingEngine:
    """Ranks candidates using configurable signal weights."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or {
            "trend_score": 0.25, "audience_demand": 0.2, "competitor_gap": 0.2,
            "knowledge_relevance": 0.15, "freshness": 0.1, "momentum": 0.1,
        }

    def rank(self, candidates: List[Any]) -> List[RankedCandidate]:
        ranked = []
        for i, c in enumerate(candidates):
            total_w = 0
            weighted_sum = 0
            for signal, weight in self._weights.items():
                val = c.signals.get(signal, c.base_score)
                weighted_sum += val * weight
                total_w += weight
            score = weighted_sum / total_w if total_w > 0 else c.base_score
            rc = RankedCandidate(c.topic, score, 0)
            rc.signal_scores = dict(c.signals)
            rc.source = c.source
            ranked.append(rc)

        ranked.sort(key=lambda r: r.final_score, reverse=True)
        for i, r in enumerate(ranked):
            r.rank = i + 1
        return ranked

    def set_weights(self, weights: Dict[str, float]) -> None:
        self._weights = weights
