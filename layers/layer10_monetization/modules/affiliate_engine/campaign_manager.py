"""CampaignManager — Niche-based affiliate campaigns with tracking and optimization."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class Campaign:
    __slots__ = ("id", "name", "niche", "status", "budget", "spent", "target_revenue",
                 "actual_revenue", "affiliate_ids", "link_ids", "platforms",
                 "start_date", "end_date", "daily_budget", "max_clicks",
                 "total_clicks", "total_conversions", "total_impressions",
                 "created_at", "updated_at", "tags", "priority")

    def __init__(self, name: str, niche: str, budget: float = 0.0,
                 target_revenue: float = 0.0, daily_budget: float = 0.0) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.niche = niche
        self.status = "active"
        self.budget = budget
        self.spent = 0.0
        self.target_revenue = target_revenue
        self.actual_revenue = 0.0
        self.affiliate_ids: List[str] = []
        self.link_ids: List[str] = []
        self.platforms: List[str] = []
        self.start_date = time.time()
        self.end_date = 0.0
        self.daily_budget = daily_budget
        self.max_clicks = 0
        self.total_clicks = 0
        self.total_conversions = 0
        self.total_impressions = 0
        self.created_at = time.time()
        self.updated_at = time.time()
        self.tags: List[str] = []
        self.priority = 5

    @property
    def roi(self) -> float:
        if self.spent == 0:
            return 0.0
        return ((self.actual_revenue - self.spent) / self.spent) * 100

    @property
    def conversion_rate(self) -> float:
        return (self.total_conversions / self.total_clicks * 100) if self.total_clicks > 0 else 0.0

    @property
    def epc(self) -> float:
        return (self.actual_revenue / self.total_clicks) if self.total_clicks > 0 else 0.0

    @property
    def ctr(self) -> float:
        return (self.total_clicks / self.total_impressions * 100) if self.total_impressions > 0 else 0.0

    @property
    def budget_utilization(self) -> float:
        return (self.spent / self.budget * 100) if self.budget > 0 else 0.0

    @property
    def revenue_progress(self) -> float:
        return (self.actual_revenue / self.target_revenue * 100) if self.target_revenue > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "niche": self.niche,
            "status": self.status, "budget": round(self.budget, 2),
            "spent": round(self.spent, 2),
            "target_revenue": round(self.target_revenue, 2),
            "actual_revenue": round(self.actual_revenue, 2),
            "roi": round(self.roi, 2),
            "total_clicks": self.total_clicks,
            "total_conversions": self.total_conversions,
            "total_impressions": self.total_impressions,
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
            "ctr": round(self.ctr, 2),
            "budget_utilization": round(self.budget_utilization, 2),
            "revenue_progress": round(self.revenue_progress, 2),
            "platforms": self.platforms,
            "priority": self.priority,
        }


class CampaignManager:
    """Manages niche-based affiliate campaigns with tracking and ROI optimization."""
    _instance: Optional["CampaignManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CampaignManager":
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
        self._campaigns: Dict[str, Campaign] = {}
        self._niche_index: Dict[str, List[str]] = {}
        self._daily_records: Dict[str, Dict[str, Dict[str, float]]] = {}

    def create_campaign(self, name: str, niche: str, budget: float = 0.0,
                        target_revenue: float = 0.0, daily_budget: float = 0.0,
                        platforms: List[str] = None, tags: List[str] = None,
                        priority: int = 5) -> Campaign:
        camp = Campaign(name, niche, budget, target_revenue, daily_budget)
        camp.platforms = platforms or []
        camp.tags = tags or []
        camp.priority = priority
        self._campaigns[camp.id] = camp
        self._niche_index.setdefault(niche, []).append(camp.id)
        return camp

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        return self._campaigns.get(campaign_id)

    def get_campaigns_by_niche(self, niche: str) -> List[Campaign]:
        ids = self._niche_index.get(niche, [])
        return [self._campaigns[i] for i in ids if i in self._campaigns]

    def get_active_campaigns(self) -> List[Campaign]:
        return [c for c in self._campaigns.values() if c.status == "active"]

    def pause_campaign(self, campaign_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if c:
            c.status = "paused"
            c.updated_at = time.time()
            return True
        return False

    def resume_campaign(self, campaign_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if c:
            c.status = "active"
            c.updated_at = time.time()
            return True
        return False

    def complete_campaign(self, campaign_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if c:
            c.status = "completed"
            c.end_date = time.time()
            c.updated_at = time.time()
            return True
        return False

    def add_link(self, campaign_id: str, link_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if c and link_id not in c.link_ids:
            c.link_ids.append(link_id)
            c.updated_at = time.time()
            return True
        return False

    def record_click(self, campaign_id: str, cost: float = 0.0) -> Optional[Campaign]:
        c = self._campaigns.get(campaign_id)
        if not c:
            return None
        c.total_clicks += 1
        c.spent += cost
        c.updated_at = time.time()
        self._record_daily(c.niche, "clicks", 1)
        return c

    def record_conversion(self, campaign_id: str, revenue: float = 0.0) -> Optional[Campaign]:
        c = self._campaigns.get(campaign_id)
        if not c:
            return None
        c.total_conversions += 1
        c.actual_revenue += revenue
        c.updated_at = time.time()
        self._record_daily(c.niche, "conversions", 1)
        self._record_daily(c.niche, "revenue", revenue)
        return c

    def record_impression(self, campaign_id: str) -> Optional[Campaign]:
        c = self._campaigns.get(campaign_id)
        if not c:
            return None
        c.total_impressions += 1
        c.updated_at = time.time()
        self._record_daily(c.niche, "impressions", 1)
        return c

    def _record_daily(self, niche: str, metric: str, value: float) -> None:
        day = time.strftime("%Y-%m-%d")
        self._daily_records.setdefault(day, {})
        self._daily_records[day].setdefault(niche, {})
        self._daily_records[day][niche][metric] = (
            self._daily_records[day][niche].get(metric, 0) + value
        )

    def get_top_campaigns(self, metric: str = "revenue", limit: int = 10) -> List[Campaign]:
        camps = list(self._campaigns.values())
        key_map = {
            "revenue": lambda c: c.actual_revenue,
            "roi": lambda c: c.roi,
            "clicks": lambda c: c.total_clicks,
            "conversions": lambda c: c.total_conversions,
            "conversion_rate": lambda c: c.conversion_rate,
            "epc": lambda c: c.epc,
        }
        fn = key_map.get(metric, key_map["revenue"])
        camps.sort(key=fn, reverse=True)
        return camps[:limit]

    def get_niche_summary(self) -> Dict[str, Dict[str, Any]]:
        summaries: Dict[str, Dict[str, Any]] = {}
        for camp in self._campaigns.values():
            n = camp.niche
            if n not in summaries:
                summaries[n] = {
                    "campaigns": 0, "total_clicks": 0, "total_conversions": 0,
                    "total_revenue": 0.0, "total_spent": 0.0,
                }
            summaries[n]["campaigns"] += 1
            summaries[n]["total_clicks"] += camp.total_clicks
            summaries[n]["total_conversions"] += camp.total_conversions
            summaries[n]["total_revenue"] += camp.actual_revenue
            summaries[n]["total_spent"] += camp.spent
        for n, s in summaries.items():
            s["total_revenue"] = round(s["total_revenue"], 2)
            s["total_spent"] = round(s["total_spent"], 2)
            s["roi"] = round(
                ((s["total_revenue"] - s["total_spent"]) / s["total_spent"] * 100)
                if s["total_spent"] > 0 else 0, 2
            )
        return summaries

    def get_campaign_status(self) -> Dict[str, Any]:
        campaigns = list(self._campaigns.values())
        return {
            "total_campaigns": len(campaigns),
            "active": sum(1 for c in campaigns if c.status == "active"),
            "paused": sum(1 for c in campaigns if c.status == "paused"),
            "completed": sum(1 for c in campaigns if c.status == "completed"),
            "total_clicks": sum(c.total_clicks for c in campaigns),
            "total_conversions": sum(c.total_conversions for c in campaigns),
            "total_revenue": round(sum(c.actual_revenue for c in campaigns), 2),
            "total_spent": round(sum(c.spent for c in campaigns), 2),
            "niches": len(self._niche_index),
            "campaigns": {c.id: c.to_dict() for c in campaigns},
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._campaigns),
            "active": sum(1 for c in self._campaigns.values() if c.status == "active"),
            "niches": len(self._niche_index),
            "daily_records": len(self._daily_records),
        }


def get_campaign_manager() -> CampaignManager:
    return CampaignManager()
