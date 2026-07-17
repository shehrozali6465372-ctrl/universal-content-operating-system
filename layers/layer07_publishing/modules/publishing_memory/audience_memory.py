"""Audience Memory — Track engagement history, audience preferences, segment insights."""
from __future__ import annotations
from typing import Any, Dict, List


class AudienceSegment:
    """A learned audience segment with preferences."""

    __slots__ = ("segment_id", "label", "preferred_content_types",
                 "avg_engagement_rate", "sample_size", "keywords")

    def __init__(self, segment_id: str = "", label: str = "") -> None:
        self.segment_id = segment_id
        self.label = label
        self.preferred_content_types: List[str] = []
        self.avg_engagement_rate: float = 0.0
        self.sample_size: int = 0
        self.keywords: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "label": self.label,
            "preferred_content_types": self.preferred_content_types,
            "avg_engagement_rate": round(self.avg_engagement_rate, 3),
            "sample_size": self.sample_size,
            "keywords": self.keywords,
        }


class AudienceMemory:
    """Track audience engagement patterns and preferences."""

    def __init__(self) -> None:
        self._segments: Dict[str, AudienceSegment] = {}
        self._engagement_history: List[Dict[str, Any]] = []
        self._content_engagement: Dict[str, List[float]] = {}

    def observe(
        self,
        content_type: str,
        platform: str,
        engagement_rate: float,
        tags: List[str] | None = None,
    ) -> None:
        self._engagement_history.append({
            "content_type": content_type,
            "platform": platform,
            "engagement_rate": engagement_rate,
        })
        self._content_engagement.setdefault(content_type, []).append(engagement_rate)

        segment_key = f"{platform}_{content_type}"
        if segment_key not in self._segments:
            self._segments[segment_key] = AudienceSegment(segment_key, f"{platform} {content_type}")
        seg = self._segments[segment_key]
        seg.sample_size += 1
        rates = self._content_engagement[content_type]
        seg.avg_engagement_rate = round(sum(rates) / max(1, len(rates)), 3)
        seg.preferred_content_types = list(set(
            ct for ct, _ in [(e["content_type"], None) for e in self._engagement_history]
        ))[:5]

    def get_segment(self, platform: str, content_type: str) -> AudienceSegment:
        key = f"{platform}_{content_type}"
        return self._segments.get(key, AudienceSegment(key, f"{platform} {content_type}"))

    def get_all_segments(self) -> List[AudienceSegment]:
        return list(self._segments.values())

    def get_best_content_type(self, platform: str = "") -> str:
        best_ct = ""
        best_rate = -1.0
        for ct, rates in self._content_engagement.items():
            avg = sum(rates) / max(1, len(rates))
            if avg > best_rate:
                best_rate = avg
                best_ct = ct
        return best_ct

    def get_avg_engagement(self, content_type: str) -> float:
        rates = self._content_engagement.get(content_type, [])
        return round(sum(rates) / max(1, len(rates)), 3) if rates else 0.0

    @property
    def segment_count(self) -> int:
        return len(self._segments)

    @property
    def history_count(self) -> int:
        return len(self._engagement_history)
