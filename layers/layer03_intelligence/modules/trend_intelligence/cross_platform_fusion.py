"""Cross-Platform Fusion — Fuses trend signals from multiple platforms."""
from __future__ import annotations
from typing import Dict, List, Optional


class CrossPlatformTrend:
    """A trend fused from multiple platform signals."""
    __slots__ = ("topic", "fused_score", "platform_scores", "platform_count",
                 "consensus_level", "dominant_platform", "confidence")

    def __init__(self, topic: str = "", fused_score: float = 0.0):
        self.topic = topic
        self.fused_score = fused_score
        self.platform_scores: Dict[str, float] = {}
        self.platform_count = 0
        self.consensus_level = 0.0
        self.dominant_platform = ""
        self.confidence = 0.0

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "fused_score": round(self.fused_score, 3),
            "platform_scores": {k: round(v, 3) for k, v in self.platform_scores.items()},
            "platform_count": self.platform_count,
            "consensus_level": round(self.consensus_level, 3),
            "dominant_platform": self.dominant_platform,
            "confidence": round(self.confidence, 3),
        }


# Platform reliability scores
PLATFORM_WEIGHTS: Dict[str, float] = {
    "google_trends": 1.0, "twitter": 0.85, "reddit": 0.8,
    "facebook": 0.75, "instagram": 0.7, "youtube": 0.85,
    "linkedin": 0.6, "tiktok": 0.8, "pinterest": 0.5,
    "news": 0.9, "quora": 0.5,
}


class CrossPlatformFusion:
    """Fuses trend signals from multiple platforms into unified scores."""

    def __init__(self, platform_weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = dict(platform_weights or PLATFORM_WEIGHTS)

    def fuse(self, topic: str, platform_data: Dict[str, float]) -> CrossPlatformTrend:
        """Fuse scores from multiple platforms.

        Args:
            topic: Trend topic
            platform_data: {platform_name: score}
        """
        result = CrossPlatformTrend(topic)
        result.platform_scores = dict(platform_data)
        result.platform_count = len(platform_data)

        if not platform_data:
            return result

        # Weighted fusion
        weighted_sum = 0.0
        weight_total = 0.0
        for platform, score in platform_data.items():
            w = self._weights.get(platform, 0.5)
            weighted_sum += score * w
            weight_total += w

        result.fused_score = weighted_sum / weight_total if weight_total > 0 else 0.0

        # Consensus: how much platforms agree (1 - normalized stdev)
        if len(platform_data) > 1:
            values = list(platform_data.values())
            mean_v = sum(values) / len(values)
            variance = sum((v - mean_v) ** 2 for v in values) / len(values)
            max_possible = max(v ** 2 for v in values) if values else 1.0
            result.consensus_level = max(0.0, 1.0 - (variance ** 0.5))
        else:
            result.consensus_level = 0.5

        # Dominant platform
        result.dominant_platform = max(platform_data, key=platform_data.get)

        # Confidence: multi-platform presence + consensus
        presence_factor = min(1.0, result.platform_count / 3.0)
        result.confidence = presence_factor * 0.5 + result.consensus_level * 0.5

        return result

    def fuse_batch(self, trends: Dict[str, Dict[str, float]]) -> List[CrossPlatformTrend]:
        return [self.fuse(topic, platforms) for topic, platforms in trends.items()]

    def find_cross_platform_trends(self, trends: List[CrossPlatformTrend],
                                    min_platforms: int = 2,
                                    min_score: float = 0.3) -> List[CrossPlatformTrend]:
        return [t for t in trends if t.platform_count >= min_platforms and t.fused_score >= min_score]
