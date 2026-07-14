"""Trend Normalizer — Normalizes trend scores across different sources."""
from __future__ import annotations
import statistics
from typing import Dict, List, Optional


class NormalizedTrend:
    """Normalized trend score with source-weighted confidence."""
    __slots__ = ("topic", "raw_score", "normalized_score", "confidence",
                 "source_count", "source_agreement")

    def __init__(self, topic: str = "", raw_score: float = 0.0,
                 normalized_score: float = 0.0, confidence: float = 0.0,
                 source_count: int = 0, source_agreement: float = 0.0):
        self.topic = topic
        self.raw_score = raw_score
        self.normalized_score = normalized_score
        self.confidence = confidence
        self.source_count = source_count
        self.source_agreement = source_agreement

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "raw_score": round(self.raw_score, 3),
            "normalized_score": round(self.normalized_score, 3),
            "confidence": round(self.confidence, 3),
            "source_count": self.source_count,
            "source_agreement": round(self.source_agreement, 3),
        }


# Source reliability weights
DEFAULT_SOURCE_WEIGHTS: Dict[str, float] = {
    "google_trends": 0.9,
    "twitter": 0.8,
    "reddit": 0.75,
    "news": 0.85,
    "facebook": 0.7,
    "youtube": 0.8,
    "linkedin": 0.7,
    "tiktok": 0.75,
    "unknown": 0.5,
}


class TrendNormalizer:
    """Normalizes raw trend scores using source weights and z-score normalization."""

    def __init__(self, source_weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = dict(source_weights or DEFAULT_SOURCE_WEIGHTS)

    def normalize(self, topic: str, scores: List[Dict[str, float]]) -> NormalizedTrend:
        """Normalize scores from multiple sources.

        Args:
            topic: The trend topic
            scores: List of {"source": str, "score": float, "volume": int}
        """
        if not scores:
            return NormalizedTrend(topic)

        raw_values = [s.get("score", 0.0) for s in scores]
        raw_avg = sum(raw_values) / len(raw_values)

        # Weighted average
        weighted_sum = 0.0
        weight_total = 0.0
        for s in scores:
            w = self._weights.get(s.get("source", "unknown"), 0.5)
            weighted_sum += s.get("score", 0.0) * w
            weight_total += w

        weighted_avg = weighted_sum / weight_total if weight_total > 0 else 0.0

        # Source agreement (low variance = high agreement)
        if len(raw_values) > 1 and raw_avg > 0:
            stdev = statistics.stdev(raw_values) if len(raw_values) > 1 else 0.0
            cv = stdev / max(raw_avg, 0.01)  # coefficient of variation
            agreement = max(0.0, 1.0 - cv)
        else:
            agreement = 0.5

        # Confidence based on source count and agreement
        source_count = len(scores)
        count_factor = min(1.0, source_count / 3.0)
        confidence = (agreement * 0.6 + count_factor * 0.4)

        return NormalizedTrend(
            topic=topic, raw_score=raw_avg, normalized_score=round(weighted_avg, 3),
            confidence=round(confidence, 3), source_count=source_count,
            source_agreement=round(agreement, 3),
        )

    def normalize_batch(self, trends: Dict[str, List[Dict[str, float]]]) -> List[NormalizedTrend]:
        return [self.normalize(topic, scores) for topic, scores in trends.items()]

    def set_source_weight(self, source: str, weight: float) -> None:
        self._weights[source] = max(0.0, min(1.0, weight))

    def get_weights(self) -> Dict[str, float]:
        return dict(self._weights)
