"""Conversion Tracker — Track clicks, CTR, signups, sales, revenue."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent


class ConversionBreakdown:
    """Detailed conversion breakdown."""

    __slots__ = ("link_clicks", "clicks", "ctr", "signups",
                 "sales", "revenue", "cost", "roas")

    def __init__(self) -> None:
        self.link_clicks: float = 0.0
        self.clicks: float = 0.0
        self.ctr: float = 0.0
        self.signups: float = 0.0
        self.sales: float = 0.0
        self.revenue: float = 0.0
        self.cost: float = 0.0
        self.roas: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_clicks": self.link_clicks,
            "clicks": self.clicks,
            "ctr": round(self.ctr, 3),
            "signups": self.signups,
            "sales": self.sales,
            "revenue": round(self.revenue, 2),
            "cost": round(self.cost, 2),
            "roas": round(self.roas, 2),
        }


class ConversionTracker:
    """Track conversion metrics from analytics events."""

    def __init__(self) -> None:
        self._tracking_count = 0

    def track(self, event: AnalyticsEvent) -> ConversionBreakdown:
        bd = ConversionBreakdown()
        bd.link_clicks = event.get("link_clicks", 0)
        bd.clicks = event.get("clicks", bd.link_clicks)
        impressions = event.get("impressions", 0) or event.get("reach", 0)
        bd.ctr = round(bd.clicks / max(1, impressions) * 100, 3)
        bd.signups = event.get("signups", 0)
        bd.sales = event.get("sales", 0)
        bd.revenue = event.get("revenue", 0)
        bd.cost = event.get("cost", 0)
        bd.roas = round(bd.revenue / max(1, bd.cost), 2) if bd.cost > 0 else 0.0
        self._tracking_count += 1
        return bd

    def track_batch(self, events: List[AnalyticsEvent]) -> List[ConversionBreakdown]:
        return [self.track(e) for e in events]

    def total_revenue(self, events: List[AnalyticsEvent]) -> float:
        return sum(e.get("revenue", 0) for e in events)

    def total_clicks(self, events: List[AnalyticsEvent]) -> float:
        return sum(e.get("clicks", 0) for e in events)

    @property
    def tracking_count(self) -> int:
        return self._tracking_count
