"""Virality Estimator — Estimate viral probability and reach multiplier."""
from __future__ import annotations
import itertools
import math
from typing import Any, Dict

from layers.layer09_learning.modules.engagement_predictor.engagement_model import EngagementPrediction

_VE_COUNTER = itertools.count(1)


class ViralityEstimate:
    """Estimate of content viral potential."""

    __slots__ = ("estimate_id", "virality_score", "virality_probability",
                 "reach_multiplier", "viral_trigger", "risk_factor",
                 "confidence")

    def __init__(self) -> None:
        self.estimate_id: str = f"ve_{next(_VE_COUNTER)}"
        self.virality_score: float = 0.0
        self.virality_probability: float = 0.0
        self.reach_multiplier: float = 1.0
        self.viral_trigger: str = ""
        self.risk_factor: float = 0.0
        self.confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimate_id": self.estimate_id,
            "virality_score": round(self.virality_score, 3),
            "virality_probability": round(self.virality_probability, 4),
            "reach_multiplier": round(self.reach_multiplier, 2),
            "viral_trigger": self.viral_trigger,
            "risk_factor": round(self.risk_factor, 3),
            "confidence": round(self.confidence, 3),
        }


class ViralityEstimator:
    """Estimate viral potential of content based on engagement signals."""

    VIRAL_TRIGGERS = {
        "controversy": 0.3,
        "emotion": 0.25,
        "humor": 0.2,
        "surprise": 0.2,
        "utility": 0.15,
        "trending": 0.3,
    }

    def estimate(self, prediction: EngagementPrediction,
                 platform: str = "") -> ViralityEstimate:
        est = ViralityEstimate()
        est.confidence = prediction.confidence

        if prediction.engagement_rate <= 0:
            return est

        # Virality score: logarithmic scale based on engagement
        engagement_total = prediction.likes + prediction.comments + prediction.shares
        est.virality_score = min(1.0, math.log1p(engagement_total) / 10)

        # Probability of virality
        est.virality_probability = min(0.95, est.virality_score * 0.8 + prediction.confidence * 0.2)

        # Reach multiplier: higher engagement rate → exponential reach boost
        if prediction.engagement_rate > 0.1:
            est.reach_multiplier = 2.0 + (prediction.engagement_rate * 5)
        elif prediction.engagement_rate > 0.05:
            est.reach_multiplier = 1.5 + (prediction.engagement_rate * 3)
        else:
            est.reach_multiplier = 1.0 + prediction.engagement_rate

        # Determine viral trigger
        if prediction.shares > prediction.likes * 0.3:
            est.viral_trigger = "high_share_ratio"
        elif prediction.comments > prediction.likes * 0.2:
            est.viral_trigger = "high_discussion"
        elif prediction.saves > prediction.likes * 0.2:
            est.viral_trigger = "high_save_rate"
        else:
            est.viral_trigger = "engagement_based"

        # Risk factor: too-fast growth can indicate spam
        est.risk_factor = min(1.0, max(0.0, est.reach_multiplier - 3.0) / 5.0)

        return est

    def estimate_viral_score(self, engagement_total: int, audience_size: int = 1000) -> float:
        """Quick virality score estimation."""
        if audience_size <= 0:
            return 0.0
        ratio = engagement_total / audience_size
        return round(min(1.0, math.log1p(ratio * 100) / 10), 3)

    def get_viral_threshold(self, platform: str = "") -> float:
        """Return the virality score threshold for a platform."""
        thresholds = {
            "tiktok": 0.3,
            "x": 0.25,
            "instagram": 0.35,
            "facebook": 0.4,
            "linkedin": 0.3,
            "youtube": 0.35,
            "reddit": 0.2,
        }
        return thresholds.get(platform.lower(), 0.3)
