"""Engagement Model — Core prediction engine for engagement metrics."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, Optional

from layers.layer09_learning.modules.engagement_predictor.feature_extractor import ContentFeatures

_EM_COUNTER = itertools.count(1)


class EngagementPrediction:
    """A prediction of engagement metrics for content."""

    __slots__ = ("prediction_id", "likes", "comments", "shares", "saves",
                 "impressions", "reach", "ctr", "engagement_rate",
                 "confidence", "horizon", "platform", "features",
                 "timestamp")

    def __init__(self) -> None:
        self.prediction_id: str = f"ep_{next(_EM_COUNTER)}"
        self.likes: float = 0.0
        self.comments: float = 0.0
        self.shares: float = 0.0
        self.saves: float = 0.0
        self.impressions: float = 0.0
        self.reach: float = 0.0
        self.ctr: float = 0.0
        self.engagement_rate: float = 0.0
        self.confidence: float = 0.5
        self.horizon: str = "24h"
        self.platform: str = ""
        self.features: Optional[ContentFeatures] = None
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "likes": round(self.likes, 1),
            "comments": round(self.comments, 1),
            "shares": round(self.shares, 1),
            "saves": round(self.saves, 1),
            "impressions": round(self.impressions, 1),
            "reach": round(self.reach, 1),
            "ctr": round(self.ctr, 4),
            "engagement_rate": round(self.engagement_rate, 4),
            "confidence": round(self.confidence, 3),
            "horizon": self.horizon,
            "platform": self.platform,
        }


class EngagementModel:
    """Predict engagement metrics using heuristic-based modeling.

    Uses content features, platform baselines, and pattern heuristics
    to estimate engagement without requiring a trained ML model.
    """

    PLATFORM_BASELINES: Dict[str, Dict[str, float]] = {
        "facebook": {"likes": 50, "comments": 5, "shares": 10, "reach": 500},
        "instagram": {"likes": 80, "comments": 8, "shares": 3, "reach": 400},
        "x": {"likes": 20, "comments": 3, "shares": 15, "reach": 600},
        "linkedin": {"likes": 30, "comments": 6, "shares": 8, "reach": 300},
        "youtube": {"likes": 40, "comments": 7, "shares": 5, "reach": 800},
        "tiktok": {"likes": 100, "comments": 10, "shares": 20, "reach": 1000},
        "pinterest": {"likes": 15, "comments": 2, "shares": 5, "reach": 200},
        "reddit": {"likes": 25, "comments": 12, "shares": 3, "reach": 400},
        "medium": {"likes": 10, "comments": 2, "shares": 3, "reach": 150},
    }

    def predict(self, features: ContentFeatures, platform: str = "",
                horizon: str = "24h", audience_size: int = 0) -> EngagementPrediction:
        pred = EngagementPrediction()
        pred.horizon = horizon
        pred.platform = platform
        pred.features = features

        baseline = self.PLATFORM_BASELINES.get(platform.lower(), self.PLATFORM_BASELINES["facebook"])
        audience_factor = max(1.0, audience_size / 1000) if audience_size > 0 else 1.0

        # Compute base engagement with content quality multipliers
        quality_multiplier = self._compute_quality_multiplier(features)
        hook_bonus = 1.3 if features.has_hook else 1.0
        cta_bonus = 1.2 if features.has_cta else 1.0
        emoji_bonus = min(1.3, 1.0 + features.emoji_count * 0.03)
        length_factor = self._compute_length_factor(features.word_count)

        total_factor = quality_multiplier * hook_bonus * cta_bonus * emoji_bonus * length_factor

        pred.likes = max(0, baseline["likes"] * total_factor * audience_factor)
        pred.comments = max(0, baseline["comments"] * total_factor * audience_factor)
        pred.shares = max(0, baseline["shares"] * total_factor * audience_factor)
        pred.saves = max(0, pred.likes * 0.15)
        pred.reach = max(0, baseline["reach"] * total_factor * audience_factor)
        pred.impressions = pred.reach * 1.3
        pred.ctr = min(1.0, (pred.likes + pred.comments + pred.shares) / max(1, pred.impressions))
        pred.engagement_rate = min(1.0, (pred.likes + pred.comments + pred.shares + pred.saves) / max(1, pred.reach))

        # Horizon scaling
        pred = self._apply_horizon_scaling(pred, horizon)

        # Confidence
        pred.confidence = self._compute_confidence(features, platform)

        return pred

    def predict_from_content(self, content: str, platform: str = "",
                             horizon: str = "24h", audience_size: int = 0,
                             content_type: str = "") -> EngagementPrediction:
        from layers.layer09_learning.modules.engagement_predictor.feature_extractor import FeatureExtractor
        extractor = FeatureExtractor()
        features = extractor.extract(content, platform, content_type)
        return self.predict(features, platform, horizon, audience_size)

    def _compute_quality_multiplier(self, f: ContentFeatures) -> float:
        multiplier = 1.0
        if f.readability_estimate > 0.7:
            multiplier *= 1.1
        if f.hashtag_count > 0 and f.hashtag_count <= 10:
            multiplier *= 1.05
        if f.question_count > 0:
            multiplier *= 1.08
        return multiplier

    def _compute_length_factor(self, word_count: int) -> float:
        if word_count < 10:
            return 0.7
        if word_count < 30:
            return 0.9
        if word_count <= 100:
            return 1.0
        if word_count <= 300:
            return 1.05
        return 0.95

    def _apply_horizon_scaling(self, pred: EngagementPrediction, horizon: str) -> EngagementPrediction:
        scales = {"immediate": 0.3, "24h": 1.0, "7d": 2.5, "30d": 5.0}
        s = scales.get(horizon, 1.0)
        pred.likes *= s
        pred.comments *= s
        pred.shares *= s
        pred.saves *= s
        pred.reach *= s
        pred.impressions *= s
        return pred

    def _compute_confidence(self, f: ContentFeatures, platform: str) -> float:
        conf = 0.5
        if platform.lower() in self.PLATFORM_BASELINES:
            conf += 0.15
        if f.word_count >= 10:
            conf += 0.1
        if f.readability_estimate > 0.5:
            conf += 0.1
        if f.has_hook:
            conf += 0.05
        if f.has_cta:
            conf += 0.05
        return round(min(0.95, conf), 3)
