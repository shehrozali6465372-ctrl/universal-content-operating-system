"""Engagement Calculator - Calculates composite engagement metrics."""
from __future__ import annotations
from typing import Dict


class EngagementResult:
    __slots__ = ("engagement_rate", "components", "score", "grade")
    def __init__(self) -> None:
        self.engagement_rate = 0.0
        self.components: Dict[str, float] = {}
        self.score = 0.0
        self.grade = ""
    def to_dict(self) -> Dict:
        return {"engagement_rate": round(self.engagement_rate, 4), "score": round(self.score, 3),
                "grade": self.grade, "components": {k: round(v, 4) for k, v in self.components.items()}}


class EngagementCalculator:
    def __init__(self, weights: Dict[str, float] = None) -> None:
        self._weights = weights or {"likes": 0.1, "comments": 0.2, "shares": 0.3,
                                     "saves": 0.2, "clicks": 0.15, "negative": -0.2}

    def calculate(self, metrics: Dict[str, float], reach: float = 1.0) -> EngagementResult:
        result = EngagementResult()
        result.components = dict(metrics)

        if reach <= 0:
            return result

        # Engagement rate
        positive = sum(metrics.get(k, 0) for k in ["likes", "comments", "shares", "saves", "clicks"])
        negative = metrics.get("negative", 0)
        result.engagement_rate = max(0, (positive - negative)) / reach

        # Composite score
        total = 0
        for metric, weight in self._weights.items():
            val = metrics.get(metric, 0) / max(reach, 1)
            total += val * weight
        result.score = max(0.0, min(1.0, total * 10))  # scale to 0-1

        # Grade
        if result.score >= 0.9: result.grade = "A+"
        elif result.score >= 0.8: result.grade = "A"
        elif result.score >= 0.7: result.grade = "B"
        elif result.score >= 0.5: result.grade = "C"
        else: result.grade = "D"
        return result
