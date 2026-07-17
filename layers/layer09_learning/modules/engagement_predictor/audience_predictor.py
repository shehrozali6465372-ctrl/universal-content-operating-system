"""Audience Predictor — Predict audience segments and engagement distribution."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

from layers.layer09_learning.modules.engagement_predictor.engagement_model import EngagementPrediction

_AP_COUNTER = itertools.count(1)


class AudienceSegment:
    """A predicted audience segment with engagement characteristics."""

    __slots__ = ("segment_id", "name", "estimated_size", "engagement_weight",
                 "preferred_content", "peak_hours")

    def __init__(self, name: str = "") -> None:
        self.segment_id: str = f"as_{next(_AP_COUNTER)}"
        self.name = name
        self.estimated_size: int = 0
        self.engagement_weight: float = 0.0
        self.preferred_content: List[str] = []
        self.peak_hours: List[int] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "estimated_size": self.estimated_size,
            "engagement_weight": round(self.engagement_weight, 3),
            "preferred_content": self.preferred_content,
            "peak_hours": self.peak_hours,
        }


class AudiencePrediction:
    """Full audience prediction result."""

    __slots__ = ("prediction_id", "segments", "total_reach",
                 "weighted_engagement_rate", "primary_segment")

    def __init__(self) -> None:
        self.prediction_id: str = f"ap_{next(_AP_COUNTER)}"
        self.segments: List[AudienceSegment] = []
        self.total_reach: int = 0
        self.weighted_engagement_rate: float = 0.0
        self.primary_segment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "segments": [s.to_dict() for s in self.segments],
            "total_reach": self.total_reach,
            "weighted_engagement_rate": round(self.weighted_engagement_rate, 4),
            "primary_segment": self.primary_segment,
        }


class AudiencePredictor:
    """Predict audience segments and engagement distribution."""

    PLATFORM_SEGMENTS: Dict[str, List[Dict[str, Any]]] = {
        "facebook": [
            {"name": "casual_browsers", "weight": 0.35, "content": ["post", "video"]},
            {"name": "community_engagers", "weight": 0.30, "content": ["group_post", "event"]},
            {"name": "news_readers", "weight": 0.20, "content": ["article", "link"]},
            {"name": "shoppers", "weight": 0.15, "content": ["product", "deal"]},
        ],
        "instagram": [
            {"name": "visual_browsers", "weight": 0.40, "content": ["reel", "carousel"]},
            {"name": "story_viewers", "weight": 0.25, "content": ["story", "reel"]},
            {"name": "shopper_audience", "weight": 0.20, "content": ["product", "carousel"]},
            {"name": "community", "weight": 0.15, "content": ["post", "live"]},
        ],
        "x": [
            {"name": "news_junkies", "weight": 0.35, "content": ["thread", "text"]},
            {"name": "debaters", "weight": 0.25, "content": ["thread", "poll"]},
            {"name": "curators", "weight": 0.25, "content": ["retweet", "bookmark"]},
            {"name": "creators", "weight": 0.15, "content": ["thread", "video"]},
        ],
        "linkedin": [
            {"name": "professionals", "weight": 0.40, "content": ["article", "post"]},
            {"name": "job_seekers", "weight": 0.25, "content": ["article", "text"]},
            {"name": "recruiters", "weight": 0.20, "content": ["post", "poll"]},
            {"name": "thought_leaders", "weight": 0.15, "content": ["article", "newsletter"]},
        ],
    }

    def predict(self, prediction: EngagementPrediction,
                platform: str = "", audience_size: int = 0) -> AudiencePrediction:
        result = AudiencePrediction()
        platform_lower = platform.lower()
        raw_segments = self.PLATFORM_SEGMENTS.get(platform_lower, self._default_segments())

        for seg_data in raw_segments:
            segment = AudienceSegment(seg_data["name"])
            segment.estimated_size = int(audience_size * seg_data["weight"]) if audience_size > 0 else 0
            segment.engagement_weight = seg_data["weight"]
            segment.preferred_content = seg_data.get("content", [])
            segment.peak_hours = self._get_segment_peak_hours(seg_data["name"])
            result.segments.append(segment)

        result.total_reach = int(prediction.reach)
        if result.segments:
            result.primary_segment = max(result.segments, key=lambda s: s.engagement_weight).name

        total_weight = sum(s.engagement_weight for s in result.segments) or 1.0
        result.weighted_engagement_rate = prediction.engagement_rate * (total_weight / len(result.segments)) if result.segments else prediction.engagement_rate

        return result

    def get_segment_count(self, platform: str = "") -> int:
        platform_lower = platform.lower()
        return len(self.PLATFORM_SEGMENTS.get(platform_lower, self._default_segments()))

    def _default_segments(self) -> List[Dict[str, Any]]:
        return [
            {"name": "general_audience", "weight": 0.50, "content": ["post"]},
            {"name": "engaged_users", "weight": 0.30, "content": ["post", "comment"]},
            {"name": "passive_viewers", "weight": 0.20, "content": ["view"]},
        ]

    def _get_segment_peak_hours(self, name: str) -> List[int]:
        hour_map = {
            "casual_browsers": [12, 19, 20, 21],
            "community_engagers": [18, 19, 20, 21],
            "news_readers": [7, 8, 12, 17],
            "visual_browsers": [12, 17, 19, 21],
            "story_viewers": [19, 20, 21, 22],
            "news_junkies": [8, 9, 12, 17],
            "debaters": [12, 18, 19, 20],
            "professionals": [7, 8, 12, 17],
        }
        return hour_map.get(name, [9, 12, 18, 20])
