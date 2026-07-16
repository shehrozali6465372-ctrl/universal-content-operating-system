"""Engagement Analyzer — Analyze likes, comments, shares, saves, engagement rate."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent


class EngagementBreakdown:
    """Detailed engagement breakdown."""

    __slots__ = ("likes", "comments", "shares", "saves", "quotes",
                 "total_engagement", "engagement_rate", "engagement_score")

    def __init__(self) -> None:
        self.likes: float = 0.0
        self.comments: float = 0.0
        self.shares: float = 0.0
        self.saves: float = 0.0
        self.quotes: float = 0.0
        self.total_engagement: float = 0.0
        self.engagement_rate: float = 0.0
        self.engagement_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "likes": self.likes, "comments": self.comments,
            "shares": self.shares, "saves": self.saves,
            "quotes": self.quotes,
            "total_engagement": self.total_engagement,
            "engagement_rate": round(self.engagement_rate, 3),
            "engagement_score": round(self.engagement_score, 2),
        }


class EngagementAnalyzer:
    """Analyze engagement metrics from analytics events."""

    WEIGHTS = {"likes": 1, "comments": 3, "shares": 5, "saves": 4, "quotes": 4}

    def __init__(self) -> None:
        self._analysis_count = 0

    def analyze(self, event: AnalyticsEvent) -> EngagementBreakdown:
        bd = EngagementBreakdown()
        bd.likes = event.get("likes", 0)
        bd.comments = event.get("comments", 0)
        bd.shares = event.get("shares", 0)
        bd.saves = event.get("saves", 0)
        bd.quotes = event.get("quotes", 0)
        bd.total_engagement = (
            bd.likes + bd.comments + bd.shares + bd.saves + bd.quotes
        )
        reach = event.get("reach", 0) or event.get("impressions", 0)
        bd.engagement_rate = round(
            bd.total_engagement / max(1, reach) * 100, 3
        )
        bd.engagement_score = round(
            (bd.likes * self.WEIGHTS["likes"] +
             bd.comments * self.WEIGHTS["comments"] +
             bd.shares * self.WEIGHTS["shares"] +
             bd.saves * self.WEIGHTS["saves"] +
             bd.quotes * self.WEIGHTS["quotes"]),
            2,
        )
        self._analysis_count += 1
        return bd

    def analyze_batch(self, events: List[AnalyticsEvent]) -> List[EngagementBreakdown]:
        return [self.analyze(e) for e in events]

    def get_top_engaged(self, events: List[AnalyticsEvent], top_n: int = 5) -> List[AnalyticsEvent]:
        scored = [(e, self.analyze(e).engagement_score) for e in events]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:top_n]]

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
