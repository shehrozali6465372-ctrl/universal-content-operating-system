"""RevenueTracker — Track all revenue streams across platforms."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_RT_COUNTER = itertools.count(1)

REVENUE_TYPES = (
    "ad_revenue", "affiliate", "sponsorship", "subscription",
    "product_sales", "donations", "course", "consulting", "other",
)


class RevenueEntry:
    """A single revenue entry."""

    __slots__ = ("entry_id", "revenue_type", "amount", "currency",
                 "platform", "source", "description", "recorded_at",
                 "metadata")

    def __init__(self, revenue_type: str = "other", amount: float = 0.0) -> None:
        self.entry_id: str = f"rev_{next(_RT_COUNTER)}"
        self.revenue_type = revenue_type if revenue_type in REVENUE_TYPES else "other"
        self.amount = max(0.0, amount)
        self.currency: str = "USD"
        self.platform: str = ""
        self.source: str = ""
        self.description: str = ""
        self.recorded_at: float = time.time()
        self.metadata: Dict[str, Any] = {}


class RevenueTracker:
    """Track revenue across all platforms and monetization models."""

    def __init__(self) -> None:
        self._entries: List[RevenueEntry] = []

    def record(self, revenue_type: str, amount: float,
               platform: str = "", source: str = "",
               description: str = "") -> RevenueEntry:
        entry = RevenueEntry(revenue_type, amount)
        entry.platform = platform
        entry.source = source
        entry.description = description
        self._entries.append(entry)
        return entry

    def get_total_revenue(self, platform: str = "",
                          revenue_type: str = "") -> float:
        entries = self._filter(platform, revenue_type)
        return round(sum(e.amount for e in entries), 2)

    def get_by_period(self, start_time: float, end_time: float,
                      platform: str = "") -> List[RevenueEntry]:
        entries = self._entries
        if platform:
            entries = [e for e in entries if e.platform == platform]
        return [e for e in entries if start_time <= e.recorded_at <= end_time]

    def get_by_type(self, revenue_type: str) -> List[RevenueEntry]:
        return [e for e in self._entries if e.revenue_type == revenue_type]

    def get_by_platform(self, platform: str) -> List[RevenueEntry]:
        return [e for e in self._entries if e.platform == platform]

    def get_daily_revenue(self, platform: str = "") -> float:
        now = time.time()
        day_ago = now - 86400
        return round(sum(e.amount for e in self.get_by_period(day_ago, now, platform)), 2)

    def get_weekly_revenue(self, platform: str = "") -> float:
        now = time.time()
        week_ago = now - 604800
        return round(sum(e.amount for e in self.get_by_period(week_ago, now, platform)), 2)

    def get_monthly_revenue(self, platform: str = "") -> float:
        now = time.time()
        month_ago = now - 2592000
        return round(sum(e.amount for e in self.get_by_period(month_ago, now, platform)), 2)

    def get_revenue_breakdown(self, platform: str = "") -> Dict[str, float]:
        entries = self._filter(platform)
        breakdown: Dict[str, float] = {}
        for e in entries:
            breakdown[e.revenue_type] = round(
                breakdown.get(e.revenue_type, 0) + e.amount, 2)
        return breakdown

    def get_entry_count(self) -> int:
        return len(self._entries)

    def _filter(self, platform: str = "",
                revenue_type: str = "") -> List[RevenueEntry]:
        entries = self._entries
        if platform:
            entries = [e for e in entries if e.platform == platform]
        if revenue_type:
            entries = [e for e in entries if e.revenue_type == revenue_type]
        return entries

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        platforms: Dict[str, int] = {}
        for e in self._entries:
            types[e.revenue_type] = types.get(e.revenue_type, 0) + 1
            if e.platform:
                platforms[e.platform] = platforms.get(e.platform, 0) + 1
        return {"total_entries": len(self._entries),
                "total_revenue": self.get_total_revenue(),
                "by_type": types, "by_platform": platforms}
