"""Reach Analyzer — Analyze reach, impressions, views, watch time."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent


class ReachBreakdown:
    """Detailed reach breakdown."""

    __slots__ = ("reach", "impressions", "views", "watch_time_minutes",
                 "completion_rate", "unique_reach", "frequency")

    def __init__(self) -> None:
        self.reach: float = 0.0
        self.impressions: float = 0.0
        self.views: float = 0.0
        self.watch_time_minutes: float = 0.0
        self.completion_rate: float = 0.0
        self.unique_reach: float = 0.0
        self.frequency: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reach": self.reach,
            "impressions": self.impressions,
            "views": self.views,
            "watch_time_minutes": round(self.watch_time_minutes, 2),
            "completion_rate": round(self.completion_rate, 3),
            "unique_reach": self.unique_reach,
            "frequency": round(self.frequency, 2),
        }


class ReachAnalyzer:
    """Analyze reach and visibility metrics."""

    def __init__(self) -> None:
        self._analysis_count = 0

    def analyze(self, event: AnalyticsEvent) -> ReachBreakdown:
        bd = ReachBreakdown()
        bd.reach = event.get("reach", 0)
        bd.impressions = event.get("impressions", 0)
        bd.views = event.get("views", 0)
        bd.watch_time_minutes = event.get("watch_time", 0) / 60 if event.get("watch_time", 0) > 0 else 0
        bd.completion_rate = event.get("completion_rate", 0)
        bd.unique_reach = event.get("unique_reach", bd.reach)
        bd.frequency = round(bd.impressions / max(1, bd.reach), 2) if bd.reach > 0 else 0
        self._analysis_count += 1
        return bd

    def analyze_batch(self, events: List[AnalyticsEvent]) -> List[ReachBreakdown]:
        return [self.analyze(e) for e in events]

    def total_reach(self, events: List[AnalyticsEvent]) -> float:
        return sum(e.get("reach", 0) for e in events)

    def total_views(self, events: List[AnalyticsEvent]) -> float:
        return sum(e.get("views", 0) for e in events)

    def avg_completion_rate(self, events: List[AnalyticsEvent]) -> float:
        rates = [e.get("completion_rate", 0) for e in events if e.get("completion_rate", 0) > 0]
        return round(sum(rates) / max(1, len(rates)), 3)

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
