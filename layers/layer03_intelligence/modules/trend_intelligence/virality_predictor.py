"""Virality Predictor — Predicts whether a trend will go viral."""
from __future__ import annotations
from typing import Dict


class ViralityResult:
    """Prediction of a trend's viral potential."""
    __slots__ = ("topic", "virality_score", "viral_probability", "risk_level",
                 "velocity_factor", "engagement_factor", "shareability_factor",
                 "timing_factor", "explanation")

    def __init__(self) -> None:
        self.topic = ""
        self.virality_score = 0.0
        self.viral_probability = 0.0
        self.risk_level = "low"
        self.velocity_factor = 0.0
        self.engagement_factor = 0.0
        self.shareability_factor = 0.0
        self.timing_factor = 0.0
        self.explanation = ""

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "virality_score": round(self.virality_score, 3),
            "viral_probability": round(self.viral_probability, 3),
            "risk_level": self.risk_level,
            "velocity_factor": round(self.velocity_factor, 3),
            "engagement_factor": round(self.engagement_factor, 3),
            "shareability_factor": round(self.shareability_factor, 3),
            "timing_factor": round(self.timing_factor, 3),
            "explanation": self.explanation,
        }


class ViralityPredictor:
    """Predicts viral potential of trends based on multiple signals."""

    def __init__(self, velocity_weight: float = 0.3, engagement_weight: float = 0.3,
                 shareability_weight: float = 0.25, timing_weight: float = 0.15) -> None:
        self._weights = {
            "velocity": velocity_weight, "engagement": engagement_weight,
            "shareability": shareability_weight, "timing": timing_weight,
        }

    def predict(self, topic: str, trend_data: Dict) -> ViralityResult:
        """Predict viral potential from trend data.

        Args:
            topic: The trend topic
            trend_data: Dict with velocity, engagement_rate, share_count,
                        comment_count, growth_rate, hours_since_peak, etc.
        """
        result = ViralityResult()
        result.topic = topic

        velocity = trend_data.get("velocity", 0.0)
        engagement_rate = trend_data.get("engagement_rate", 0.0)
        share_count = trend_data.get("share_count", 0)
        comment_count = trend_data.get("comment_count", 0)
        growth_rate = trend_data.get("growth_rate", 0.0)
        hours_since_peak = trend_data.get("hours_since_peak", 48)

        # Velocity factor (0-1)
        result.velocity_factor = min(1.0, max(0.0, velocity / 100.0))

        # Engagement factor (likes + comments + shares normalized)
        total_engagement = engagement_rate * 1000 + share_count + comment_count
        result.engagement_factor = min(1.0, total_engagement / 10000.0)

        # Shareability factor
        share_ratio = share_count / max(comment_count + 1, 1)
        result.shareability_factor = min(1.0, share_ratio)

        # Timing factor (freshness bonus)
        result.timing_factor = max(0.0, min(1.0, 1.0 - hours_since_peak / 168.0))

        # Growth rate bonus
        growth_bonus = min(0.2, growth_rate * 0.02)

        # Weighted virality score
        result.virality_score = min(1.0, (
            result.velocity_factor * self._weights["velocity"]
            + result.engagement_factor * self._weights["engagement"]
            + result.shareability_factor * self._weights["shareability"]
            + result.timing_factor * self._weights["timing"]
            + growth_bonus
        ))

        # Viral probability
        result.viral_probability = self._sigmoid(result.virality_score * 4 - 2)

        # Risk level
        if result.viral_probability > 0.7:
            result.risk_level = "high"
        elif result.viral_probability > 0.4:
            result.risk_level = "medium"
        else:
            result.risk_level = "low"

        # Explanation
        factors = []
        if result.velocity_factor > 0.5:
            factors.append("high velocity")
        if result.engagement_factor > 0.5:
            factors.append("strong engagement")
        if result.shareability_factor > 0.5:
            factors.append("high shareability")
        if result.timing_factor > 0.5:
            factors.append("fresh content")
        if growth_bonus > 0.1:
            factors.append("rapid growth")
        result.explanation = "Viral factors: " + ", ".join(factors) if factors else "Low viral signals"

        return result

    def _sigmoid(self, x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, x))))


import math
