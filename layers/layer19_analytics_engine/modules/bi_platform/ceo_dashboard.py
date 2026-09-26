"""CEODashboard — Total revenue, accounts, profit, growth, AI health score."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .validation import require_date, require_finite_number, require_non_negative_int


class DailySnapshot:
    __slots__ = ("date", "total_revenue", "affiliate_revenue", "ad_revenue", "total_expenses", "profit", "new_accounts", "active_accounts", "total_posts", "total_clicks", "total_conversions", "ai_health_score", "metadata")

    def __init__(self, date: str = "") -> None:
        self.date = date or time.strftime("%Y-%m-%d")
        self.total_revenue = 0.0; self.affiliate_revenue = 0.0; self.ad_revenue = 0.0
        self.total_expenses = 0.0; self.profit = 0.0; self.new_accounts = 0; self.active_accounts = 0
        self.total_posts = 0; self.total_clicks = 0; self.total_conversions = 0; self.ai_health_score = 0.0
        self.metadata: Dict[str, Any] = {}

    @property
    def profit_margin(self) -> float:
        return (self.profit / self.total_revenue * 100) if self.total_revenue > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.total_conversions / self.total_clicks * 100) if self.total_clicks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "revenue": round(self.total_revenue, 2), "affiliate": round(self.affiliate_revenue, 2), "ads": round(self.ad_revenue, 2), "expenses": round(self.total_expenses, 2), "profit": round(self.profit, 2), "profit_margin": round(self.profit_margin, 1), "accounts": self.active_accounts, "posts": self.total_posts, "clicks": self.total_clicks, "conversions": self.total_conversions, "conversion_rate": round(self.conversion_rate, 2), "ai_health": round(self.ai_health_score, 1)}


class CEODashboard:
    _instance: Optional["CEODashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CEODashboard":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls); cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized: return
        self._initialized = True
        self._data_lock = threading.RLock()
        self._snapshots: Dict[str, DailySnapshot] = {}
        self._totals = {"total_revenue": 0, "affiliate_revenue": 0, "ad_revenue": 0, "total_expenses": 0, "total_profit": 0, "total_accounts": 0, "total_posts": 0, "total_clicks": 0, "total_conversions": 0}
        self._kpi_targets: Dict[str, float] = {}; self._alert_rules: List[Dict[str, Any]] = []

    def record_snapshot(self, snapshot: DailySnapshot) -> None:
        if not isinstance(snapshot, DailySnapshot):
            raise TypeError("snapshot must be a DailySnapshot")
        require_date(snapshot.date)
        for field in ("total_revenue", "affiliate_revenue", "ad_revenue", "total_expenses"):
            require_finite_number(getattr(snapshot, field), field, minimum=0.0)
        for field in ("new_accounts", "active_accounts", "total_posts", "total_clicks", "total_conversions"):
            require_non_negative_int(getattr(snapshot, field), field)
        with self._data_lock:
            old = self._snapshots.get(snapshot.date)
            if old is not None:
                self._totals["total_revenue"] -= old.total_revenue
                self._totals["affiliate_revenue"] -= old.affiliate_revenue
                self._totals["ad_revenue"] -= old.ad_revenue
                self._totals["total_expenses"] -= old.total_expenses
                self._totals["total_profit"] -= old.profit
                self._totals["total_posts"] -= old.total_posts
                self._totals["total_clicks"] -= old.total_clicks
                self._totals["total_conversions"] -= old.total_conversions
            self._snapshots[snapshot.date] = snapshot
            self._totals["total_revenue"] += snapshot.total_revenue
            self._totals["affiliate_revenue"] += snapshot.affiliate_revenue
            self._totals["ad_revenue"] += snapshot.ad_revenue
            self._totals["total_expenses"] += snapshot.total_expenses
            self._totals["total_profit"] += snapshot.profit
            self._totals["total_posts"] += snapshot.total_posts
            self._totals["total_clicks"] += snapshot.total_clicks
            self._totals["total_conversions"] += snapshot.total_conversions
            self._totals["total_accounts"] = max(
                self._totals["total_accounts"], snapshot.active_accounts
            )

    def record_daily(self, date: str = "", revenue: float = 0.0, affiliate_rev: float = 0.0, ad_rev: float = 0.0, expenses: float = 0.0, active_accounts: int = 0, posts: int = 0, clicks: int = 0, conversions: int = 0, ai_health: float = 100.0) -> DailySnapshot:
        if date:
            date = require_date(date)
        revenue = require_finite_number(revenue, "revenue", minimum=0.0)
        affiliate_rev = require_finite_number(affiliate_rev, "affiliate_rev", minimum=0.0)
        ad_rev = require_finite_number(ad_rev, "ad_rev", minimum=0.0)
        expenses = require_finite_number(expenses, "expenses", minimum=0.0)
        for value, field in ((active_accounts, "active_accounts"), (posts, "posts"), (clicks, "clicks"), (conversions, "conversions")):
            require_non_negative_int(value, field)
        ai_health = require_finite_number(ai_health, "ai_health", minimum=0.0)
        if ai_health > 100.0:
            raise ValueError("ai_health must be <= 100")
        snap = DailySnapshot(date); snap.total_revenue = revenue; snap.affiliate_revenue = affiliate_rev; snap.ad_revenue = ad_rev
        snap.total_expenses = expenses; snap.profit = revenue - expenses; snap.active_accounts = active_accounts; snap.total_posts = posts
        snap.total_clicks = clicks; snap.total_conversions = conversions; snap.ai_health_score = ai_health; self.record_snapshot(snap); return snap

    def get_today(self) -> Optional[DailySnapshot]:
        with self._data_lock:
            return self._snapshots.get(time.strftime("%Y-%m-%d"))

    def get_recent(self, days: int = 30) -> List[DailySnapshot]:
        require_non_negative_int(days, "days")
        with self._data_lock:
            return [self._snapshots[d] for d in sorted(self._snapshots.keys(), reverse=True)[:days]]

    def get_monthly_summary(self) -> Dict[str, Any]:
        month = time.strftime("%Y-%m")
        with self._data_lock:
            snapshots = list(self._snapshots.values())
        monthly = [s for s in snapshots if s.date.startswith(month)]
        if not monthly and snapshots:
            month = sorted(s.date for s in snapshots)[-1][:7]
            monthly = [s for s in snapshots if s.date.startswith(month)]
        if not monthly:
            return {"month": month, "days": 0}
        return {
            "month": month,
            "days": len(monthly),
            "total_revenue": round(sum(s.total_revenue for s in monthly), 2),
            "total_profit": round(sum(s.profit for s in monthly), 2),
            "avg_daily_revenue": round(sum(s.total_revenue for s in monthly) / len(monthly), 2),
            "avg_profit_margin": round(sum(s.profit_margin for s in monthly) / len(monthly), 1),
            "total_posts": sum(s.total_posts for s in monthly),
            "total_clicks": sum(s.total_clicks for s in monthly),
            "total_conversions": sum(s.total_conversions for s in monthly),
        }

    def get_growth_metrics(self) -> Dict[str, Any]:
        with self._data_lock:
            snapshots = dict(self._snapshots)
        dates = sorted(snapshots)
        if len(dates) < 2:
            return {"daily_growth": 0, "weekly_growth": 0, "monthly_growth": 0}
        recent = snapshots[dates[-1]]
        prev = snapshots[dates[-2]]
        daily = ((recent.total_revenue - prev.total_revenue) / prev.total_revenue * 100) if prev.total_revenue > 0 else 0
        week = snapshots[dates[max(0, len(dates) - 7)]]
        weekly = ((recent.total_revenue - week.total_revenue) / week.total_revenue * 100) if week.total_revenue > 0 else 0
        return {
            "daily_growth": round(daily, 1),
            "weekly_growth": round(weekly, 1),
            "current_revenue": round(recent.total_revenue, 2),
            "current_profit": round(recent.profit, 2),
            "current_ai_health": round(recent.ai_health_score, 1),
        }

    def set_kpi_target(self, metric: str, target: float) -> None:
        if not metric or not metric.strip():
            raise ValueError("metric must be non-blank")
        target = require_finite_number(target, "target", minimum=0.0)
        with self._data_lock:
            self._kpi_targets[metric.strip()] = target

    def get_kpi_status(self) -> Dict[str, Any]:
        with self._data_lock:
            totals = dict(self._totals)
            targets = dict(self._kpi_targets)
        return {
            metric: {
                "current": round(totals.get(metric, 0), 2),
                "target": target,
                "progress": round((totals.get(metric, 0) / target * 100) if target > 0 else 0, 1),
            }
            for metric, target in targets.items()
        }

    def get_ceo_summary(self) -> Dict[str, Any]:
        with self._data_lock:
            totals = dict(self._totals)
        recent = self.get_recent(7)
        latest = recent[0] if recent else None
        return {
            "total_revenue": round(totals["total_revenue"], 2),
            "total_profit": round(totals["total_profit"], 2),
            "total_accounts": totals["total_accounts"],
            "total_posts": totals["total_posts"],
            "total_clicks": totals["total_clicks"],
            "total_conversions": totals["total_conversions"],
            "overall_conversion_rate": round(
                (totals["total_conversions"] / totals["total_clicks"] * 100)
                if totals["total_clicks"] > 0 else 0, 2
            ),
            "today_revenue": round(latest.total_revenue, 2) if latest else 0,
            "today_profit": round(latest.profit, 2) if latest else 0,
            "ai_health": round(latest.ai_health_score, 1) if latest else 0,
            "growth": self.get_growth_metrics(),
            "monthly": self.get_monthly_summary(),
            "kpis": self.get_kpi_status(),
        }

    def stats(self) -> Dict[str, Any]:
        with self._data_lock:
            return {"snapshots": len(self._snapshots), "totals": dict(self._totals)}


def get_ceo_dashboard() -> CEODashboard:
    return CEODashboard()
