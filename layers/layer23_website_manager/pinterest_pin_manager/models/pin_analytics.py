"""PinAnalytics — Performance metrics for a Pinterest Pin."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PinAnalytics:
    """Daily pin performance snapshot."""

    analytics_id: str = field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    pin_id: str = ""
    date: float = field(default_factory=time.time)

    impressions: int = 0
    saves: int = 0
    clicks: int = 0
    outbound_clicks: int = 0
    closeups: int = 0

    @property
    def ctr(self) -> float:
        total = self.impressions or 1
        return round((self.clicks / total) * 100, 2)

    @property
    def save_rate(self) -> float:
        total = self.impressions or 1
        return round((self.saves / total) * 100, 2)

    @property
    def engagement_rate(self) -> float:
        total = self.impressions or 1
        engaged = self.saves + self.clicks + self.closeups
        return round((engaged / total) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analytics_id": self.analytics_id,
            "pin_id": self.pin_id,
            "date": self.date,
            "impressions": self.impressions,
            "saves": self.saves,
            "clicks": self.clicks,
            "outbound_clicks": self.outbound_clicks,
            "ctr": self.ctr,
            "save_rate": self.save_rate,
            "engagement_rate": self.engagement_rate,
        }

    @classmethod
    def aggregate(cls, records: list["PinAnalytics"]) -> "PinAnalytics":
        if not records:
            return cls()
        return cls(
            impressions=sum(r.impressions for r in records),
            saves=sum(r.saves for r in records),
            clicks=sum(r.clicks for r in records),
            outbound_clicks=sum(r.outbound_clicks for r in records),
            closeups=sum(r.closeups for r in records),
        )
