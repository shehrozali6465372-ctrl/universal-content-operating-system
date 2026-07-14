"""Trend Confidence - Confidence scoring for trend analysis results."""
from __future__ import annotations
from typing import Dict, List


class TrendConfidenceResult:
    """Confidence assessment for a trend analysis."""
    __slots__ = ("topic", "overall_confidence", "data_confidence", "source_confidence",
                 "recency_confidence", "consistency_confidence", "risk_level",
                 "factors", "explanation")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.overall_confidence = 0.0
        self.data_confidence = 0.0
        self.source_confidence = 0.0
        self.recency_confidence = 0.0
        self.consistency_confidence = 0.0
        self.risk_level = "medium"
        self.factors: List[str] = []
        self.explanation = ""

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "overall_confidence": round(self.overall_confidence, 3),
            "data_confidence": round(self.data_confidence, 3),
            "source_confidence": round(self.source_confidence, 3),
            "recency_confidence": round(self.recency_confidence, 3),
            "consistency_confidence": round(self.consistency_confidence, 3),
            "risk_level": self.risk_level,
            "factors": list(self.factors), "explanation": self.explanation,
        }


class TrendConfidence:
    """Calculates confidence for trend analysis results."""

    def __init__(self, data_weight: float = 0.3, source_weight: float = 0.25,
                 recency_weight: float = 0.25, consistency_weight: float = 0.2) -> None:
        self._weights = {
            "data": data_weight, "source": source_weight,
            "recency": recency_weight, "consistency": consistency_weight,
        }

    def calculate(self, topic: str, signals: Dict) -> TrendConfidenceResult:
        """Calculate confidence from multiple trend signals."""
        result = TrendConfidenceResult(topic)
        factors = []

        data_points = signals.get("data_points", 0)
        result.data_confidence = min(1.0, data_points / 10.0)
        if result.data_confidence > 0.7:
            factors.append(f"Rich data ({data_points} points)")
        elif result.data_confidence < 0.3:
            factors.append(f"Limited data ({data_points} points)")

        source_count = signals.get("source_count", 0)
        result.source_confidence = min(1.0, source_count / 3.0)

        hours_old = signals.get("hours_since_latest", 48)
        result.recency_confidence = max(0.0, 1.0 - hours_old / 168.0)

        score_variance = signals.get("score_variance", 0.5)
        result.consistency_confidence = max(0.0, 1.0 - score_variance)

        result.overall_confidence = (
            result.data_confidence * self._weights["data"]
            + result.source_confidence * self._weights["source"]
            + result.recency_confidence * self._weights["recency"]
            + result.consistency_confidence * self._weights["consistency"]
        )

        if result.overall_confidence >= 0.7:
            result.risk_level = "low"
        elif result.overall_confidence >= 0.4:
            result.risk_level = "medium"
        else:
            result.risk_level = "high"

        result.factors = factors
        result.explanation = (
            f"Confidence: {result.overall_confidence:.0%} "
            f"(data: {result.data_confidence:.0%}, source: {result.source_confidence:.0%}, "
            f"recency: {result.recency_confidence:.0%}, consistency: {result.consistency_confidence:.0%})"
        )
        return result
