"""AudienceInsight — Deep audience segmentation and insights."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AI_COUNTER = itertools.count(1)


class AudienceSegment:
    """An audience segment with engagement characteristics."""

    __slots__ = ("segment_id", "label", "size", "engagement_rate",
                 "preferred_content_types", "active_hours", "active_days",
                 "languages", "platform", "created_at")

    def __init__(self, label: str = "") -> None:
        self.segment_id: str = f"aseg_{next(_AI_COUNTER)}"
        self.label = label
        self.size: int = 0
        self.engagement_rate: float = 0.0
        self.preferred_content_types: List[str] = []
        self.active_hours: List[int] = []
        self.active_days: List[int] = []
        self.languages: List[str] = []
        self.platform: str = ""
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"segment_id": self.segment_id, "label": self.label, "size": self.size,
                "engagement_rate": round(self.engagement_rate, 4),
                "platform": self.platform}


class AudienceInsight:
    """Audience intelligence — segment, analyze, and learn from audience."""
    def __init__(self) -> None:
        self._segments: List[AudienceSegment] = []
        self._behavior_insights: List[Dict[str, Any]] = []
        self._sentiment_data: Dict[str, List[float]] = {}

    def create_segment(self, label: str, platform: str = "") -> AudienceSegment:
        segment = AudienceSegment(label)
        segment.platform = platform
        self._segments.append(segment)
        return segment

    def get_segment(self, segment_id: str) -> Optional[AudienceSegment]:
        for s in self._segments:
            if s.segment_id == segment_id:
                return s
        return None

    def get_segments(self, platform: str = "") -> List[AudienceSegment]:
        if platform:
            return [s for s in self._segments if s.platform == platform]
        return list(self._segments)

    def update_segment(self, segment_id: str, data: Dict[str, Any]) -> bool:
        segment = self.get_segment(segment_id)
        if segment is None:
            return False
        for k, v in data.items():
            if hasattr(segment, k):
                setattr(segment, k, v)
        return True

    def record_sentiment(self, platform: str, value: float) -> None:
        if platform not in self._sentiment_data:
            self._sentiment_data[platform] = []
        self._sentiment_data[platform].append(value)

    def get_avg_sentiment(self, platform: str = "") -> float:
        if platform:
            values = self._sentiment_data.get(platform, [])
        else:
            values = [v for lst in self._sentiment_data.values() for v in lst]
        if not values:
            return 0.0
        return round(sum(values) / len(values), 3)

    def add_behavior_insight(self, insight: Dict[str, Any]) -> None:
        self._behavior_insights.append(insight)

    def get_behavior_insights(self, platform: str = "") -> List[Dict[str, Any]]:
        if platform:
            return [i for i in self._behavior_insights if i.get("platform") == platform]
        return list(self._behavior_insights)

    def analyze(self) -> Dict[str, Any]:
        return {
            "total_segments": len(self._segments),
            "avg_segment_size": round(sum(s.size for s in self._segments) / max(1, len(self._segments)), 0),
            "behavior_insights_count": len(self._behavior_insights),
        }

    def get_stats(self) -> Dict[str, Any]:
        return self.analyze()
