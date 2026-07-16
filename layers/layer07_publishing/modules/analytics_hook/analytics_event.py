"""Analytics Event — Unified analytics event model across all platforms."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict

_EVENT_COUNTER = itertools.count(1)


class AnalyticsEvent:
    """A single analytics data point from a published post."""

    __slots__ = (
        "event_id", "platform", "post_id", "content_id",
        "timestamp", "collected_at", "metrics", "metadata",
        "engagement", "reach", "conversion",
    )

    def __init__(
        self,
        platform: str = "",
        post_id: str = "",
        content_id: str = "",
    ) -> None:
        self.event_id: str = f"evt_{next(_EVENT_COUNTER)}"
        self.platform = platform
        self.post_id = post_id
        self.content_id = content_id
        self.timestamp: float = time.time()
        self.collected_at: float = time.time()
        self.metrics: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.engagement: Dict[str, float] = {}
        self.reach: Dict[str, float] = {}
        self.conversion: Dict[str, float] = {}

    def get(self, key: str, default: float = 0.0) -> float:
        return float(self.metrics.get(key, default))

    def set_metric(self, key: str, value: float) -> None:
        self.metrics[key] = value

    def merge(self, other: "AnalyticsEvent") -> None:
        self.metrics.update(other.metrics)
        self.engagement.update(other.engagement)
        self.reach.update(other.reach)
        self.conversion.update(other.conversion)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "platform": self.platform,
            "post_id": self.post_id,
            "content_id": self.content_id,
            "timestamp": self.timestamp,
            "collected_at": self.collected_at,
            "metrics": self.metrics,
            "engagement": self.engagement,
            "reach": self.reach,
            "conversion": self.conversion,
        }
