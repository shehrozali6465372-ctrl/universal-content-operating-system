"""CEODashboard — Total revenue, accounts, profit, growth, AI health score."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class DailySnapshot:
    __slots__ = ("date", "total_revenue", "affiliate_revenue", "ad_revenue",
                 "total_expenses", "profit", "new_accounts", "active_accounts",
                 "total_posts", "total_clicks", "total_conversions",
                 "ai_health_score", "metadata")

    def __init__(self, date: str = "") -> None:
        self.date = date or time.strftime("%Y-%m-%d")
        self.total_revenue = 0.0
        self.affiliate_revenue = 0.0
        self.ad_revenue = 0.0
        self.total_expenses = 0.0
        self.profit = 0.0
        self.new_accounts = 0
        self.active_accounts = 0
        self.total_posts = 0
        self.total_clicks = 0
        self.total_conversions = 0
        self.ai_health_score = 0.0
        self.metadata: Dict[str, Any] = {}

    @property
    def profit_margin(self) -> float:
        return (self.profit / self.total_revenue * 100) if self.total_revenue > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.total_conversions / self.total_clicks * 100) if self.total_clicks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "revenue": round(self.total_revenue, 2),
            "affiliate": round(self.affiliate_revenue, 2),
            "ads": round(self.ad_revenue, 2),
            "expenses": round(self.total_expenses, 2),
            "profit": round(self.profit, 2),
            "profit_margin": round(self.profit_margin, 1),
            "accounts": self.active_accounts,
            "posts": self.total_posts,
            "clicks": self.total_clicks,
            "conversions": self.total_conversions,
            "conversion_rate": round(self.conversion_rate, 2),
            "ai_health": round(self.ai_health_score, 1),
        }


class CEODashboard:
    """Executive dashboard: revenue, profit, growth, AI health for CEO view."""
    _instance: Optional["CEODashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CEODashboard":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._snapshots: Dict[str, DailySnapshot] = {}
        self._totals: Dict[str, float] = {
            "total_revenue": 0, "affiliate_revenue": 0, "ad_revenue": 0,
            "total_expenses": 0, "total_profit": 0, "total_accounts": 0,
            "total_posts": 0, "total_clicks": 0, "total_conversions": 0,
        }
        self._kpi_targets: Dict[str, float] = {}
        self._alert_rules: List[Dict[str, Any]] = []

    def record_snapshot(self, snapshot: DailySnapshot) -> None:
        self._snapshots[snapshot.date] = snapshot
        self._totals["total_revenue"] += snapshot.total_revenue
        self._totals["affiliate_revenue"] += snapshot.affiliate_revenue
        self._totals["ad_revenue"] += snapshot.ad_revenue
        self._totals["total_expenses"] += snapshot.total_expenses
        self._totals["total_profit"] += snapshot.profit
        self._totals["total_posts"] += snapshot.total_posts
        self._totals["total_clicks"] += snapshot.total_clicks
        self._totals["total_conversions"] += snapshot.total_conversions

    def record_daily(self, date: str = "", revenue: float = 0.0,
                     affiliate_rev: float = 0.0, ad_rev: float = 0.0,
                     expenses: float = 0.0, active_accounts: int = 0,
                     posts: int = 0, clicks: int = 0, conversions: int = 0,
                     ai_health: float = 100.0) -> DailySnapshot:
        snap = DailySnapshot(date)
        snap.total_revenue = revenue
        snap.affiliate_revenue = affiliate_rev
        snap.ad_revenue = ad_rev
        snap.total_expenses = expenses
        snap.profit = revenue - expenses
        snap.active_accounts = active_accounts
        snap.total_posts = posts
        snap.total_clicks = clicks
        snap.total_conversions = conversions
        snap.ai_health_score = ai_health
        self.record_snapshot(snap)
        return snap

    def get_today(self) -> Optional[DailySnapshot]:
        today = time.strftime("%Y-%m-%d")
        return self._snapshots.get(today)

    def get_recent(self, days: int = 30) -> List[DailySnapshot]:
        dates = sorted(self._snapshots.keys(), reverse=True)[:days]
        return [self._snapshots[d] for d in dates]

    def get_monthly_summary(self) -> Dict[str, Any]:
        month = time.strftime("%Y-%m")
        monthly = [s for s in self._snapshots.values() if s.date.startswith(month)]
        if not monthly:
            return {"month": month, "days": 0}
        return {
            "month": month, "days": len(monthly),
            "total_revenue": round(sum(s.total_revenue for s in monthly), 2),
            "total_profit": round(sum(s.profit for s in monthly), 2),
            "avg_daily_revenue": round(sum(s.total_revenue for s in monthly) / len(monthly), 2),
            "avg_profit_margin": round(
                sum(s.profit_margin for s in monthly) / len(monthly), 1
            ),
            "total_posts": sum(s.total_posts for s in monthly),
            "total_clicks": sum(s.total_clicks for s in monthly),
            "total_conversions": sum(s.total_conversions for s in monthly),
        }

    def get_growth_metrics(self) -> Dict[str, Any]:
        dates = sorted(self._snapshots.keys())
        if len(dates) < 2:
            return {"daily_growth": 0, "weekly_growth": 0, "monthly_growth": 0}
        recent = self._snapshots[dates[-1]]
        prev = self._snapshots[dates[-2]]
        daily_growth = ((recent.total_revenue - prev.total_revenue) / prev.total_revenue * 100
                       ) if prev.total_revenue > 0 else 0
        week_ago_idx = max(0, len(dates) - 7)
        week_ago = self._snapshots[dates[week_ago_idx]]
        weekly_growth = ((recent.total_revenue - week_ago.total_revenue) / week_ago.total_revenue * 100
                        ) if week_ago.total_revenue > 0 else 0
        return {
            "daily_growth": round(daily_growth, 1),
            "weekly_growth": round(weekly_growth, 1),
            "current_revenue": round(recent.total_revenue, 2),
            "current_profit": round(recent.profit, 2),
            "current_ai_health": round(recent.ai_health_score, 1),
        }

    def set_kpi_target(self, metric: str, target: float) -> None:
        self._kpi_targets[metric] = target

    def get_kpi_status(self) -> Dict[str, Any]:
        result = {}
        for metric, target in self._kpi_targets.items():
            current = self._totals.get(metric, 0)
            result[metric] = {
                "current": round(current, 2),
                "target": target,
                "progress": round((current / target * 100) if target > 0 else 0, 1),
            }
        return result

    def get_ceo_summary(self) -> Dict[str, Any]:
        recent = self.get_recent(7)
        latest = recent[0] if recent else None
        return {
            "total_revenue": round(self._totals["total_revenue"], 2),
            "total_profit": round(self._totals["total_profit"], 2),
            "total_accounts": self._totals["total_accounts"],
            "total_posts": self._totals["total_posts"],
            "total_clicks": self._totals["total_clicks"],
            "total_conversions": self._totals["total_conversions"],
            "overall_conversion_rate": round(
                (self._totals["total_conversions"] / self._totals["total_clicks"] * 100)
                if self._totals["total_clicks"] > 0 else 0, 2
            ),
            "today_revenue": round(latest.total_revenue, 2) if latest else 0,
            "today_profit": round(latest.profit, 2) if latest else 0,
            "ai_health": round(latest.ai_health_score, 1) if latest else 0,
            "growth": self.get_growth_metrics(),
            "monthly": self.get_monthly_summary(),
            "kpis": self.get_kpi_status(),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "snapshots": len(self._snapshots),
            "totals": self._totals,
        }


def get_ceo_dashboard() -> CEODashboard:
    return CEODashboard()
