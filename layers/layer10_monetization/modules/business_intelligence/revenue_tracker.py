"""RevenueTracker — append-only validated revenue ledger."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_RT_COUNTER = itertools.count(1)
REVENUE_TYPES = ("ad_revenue", "affiliate", "sponsorship", "subscription",
                 "product_sales", "donations", "course", "consulting", "other")


class RevenueEntry:
    def __init__(self, revenue_type: str = "other", amount: float = 0.0) -> None:
        self.entry_id = f"rev_{next(_RT_COUNTER)}"
        self.revenue_type = revenue_type if revenue_type in REVENUE_TYPES else "other"
        self.amount = float(amount)
        self.currency = "USD"
        self.platform = ""
        self.source = ""
        self.description = ""
        self.recorded_at = time.time()
        self.metadata: Dict[str, Any] = {}


class RevenueTracker:
    def __init__(self, max_entries: int = 100000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._entries: List[RevenueEntry] = []

    def record(self, revenue_type: str, amount: float, platform: str = "",
               source: str = "", description: str = "") -> RevenueEntry:
        if amount < 0:
            raise ValueError("revenue amount must be non-negative")
        entry = RevenueEntry(revenue_type, amount)
        entry.platform, entry.source, entry.description = platform, source, description
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            del self._entries[:-self._max_entries]
        return entry

    def get_total_revenue(self, platform: str = "", revenue_type: str = "") -> float:
        return round(sum(e.amount for e in self._filter(platform, revenue_type)), 2)

    def get_by_period(self, start_time: float, end_time: float, platform: str = "") -> List[RevenueEntry]:
        if start_time > end_time:
            raise ValueError("start_time must not exceed end_time")
        return [e for e in self._entries if start_time <= e.recorded_at <= end_time
                and (not platform or e.platform == platform)]

    def get_by_type(self, revenue_type: str) -> List[RevenueEntry]:
        return [e for e in self._entries if e.revenue_type == revenue_type]

    def get_by_platform(self, platform: str) -> List[RevenueEntry]:
        return [e for e in self._entries if e.platform == platform]

    def get_daily_revenue(self, platform: str = "") -> float:
        now = time.time()
        return round(sum(e.amount for e in self.get_by_period(now - 86400, now, platform)), 2)

    def get_weekly_revenue(self, platform: str = "") -> float:
        now = time.time()
        return round(sum(e.amount for e in self.get_by_period(now - 604800, now, platform)), 2)

    def get_monthly_revenue(self, platform: str = "") -> float:
        now = time.time()
        return round(sum(e.amount for e in self.get_by_period(now - 2592000, now, platform)), 2)

    def get_revenue_breakdown(self, platform: str = "") -> Dict[str, float]:
        breakdown: Dict[str, float] = {}
        for entry in self._filter(platform):
            breakdown[entry.revenue_type] = round(breakdown.get(entry.revenue_type, 0.0) + entry.amount, 2)
        return breakdown

    def get_entry_count(self) -> int:
        return len(self._entries)

    def _filter(self, platform: str = "", revenue_type: str = "") -> List[RevenueEntry]:
        return [e for e in self._entries
                if (not platform or e.platform == platform)
                and (not revenue_type or e.revenue_type == revenue_type)]

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        platforms: Dict[str, int] = {}
        for entry in self._entries:
            types[entry.revenue_type] = types.get(entry.revenue_type, 0) + 1
            if entry.platform:
                platforms[entry.platform] = platforms.get(entry.platform, 0) + 1
        return {"total_entries": len(self._entries), "total_revenue": self.get_total_revenue(),
                "by_type": types, "by_platform": platforms}
