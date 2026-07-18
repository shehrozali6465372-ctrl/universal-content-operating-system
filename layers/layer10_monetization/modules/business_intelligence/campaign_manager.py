"""CampaignManager — Manage marketing and sponsorship campaigns."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_CM_COUNTER = itertools.count(1)

CAMPAIGN_TYPES = (
    "marketing", "sponsorship", "product_launch", "seasonal",
    "cross_platform", "brand_awareness", "lead_gen", "retargeting",
)

CAMPAIGN_STATUSES = ("draft", "planned", "active", "paused", "completed", "cancelled")


class Campaign:
    """A marketing or sponsorship campaign."""

    __slots__ = ("campaign_id", "name", "campaign_type", "status",
                 "platforms", "budget", "spent", "revenue",
                 "start_date", "end_date", "goals", "metrics",
                 "created_at")

    def __init__(self, name: str = "", campaign_type: str = "marketing") -> None:
        self.campaign_id: str = f"camp_{next(_CM_COUNTER)}"
        self.name = name
        self.campaign_type = campaign_type if campaign_type in CAMPAIGN_TYPES else "marketing"
        self.status: str = "draft"
        self.platforms: List[str] = []
        self.budget: float = 0.0
        self.spent: float = 0.0
        self.revenue: float = 0.0
        self.start_date: float = 0.0
        self.end_date: float = 0.0
        self.goals: List[str] = []
        self.metrics: Dict[str, Any] = {}
        self.created_at: float = time.time()

    def get_roi(self) -> float:
        if self.spent == 0:
            return 0.0
        return round((self.revenue - self.spent) / self.spent, 4)

    def get_remaining_budget(self) -> float:
        return round(max(0.0, self.budget - self.spent), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {"campaign_id": self.campaign_id, "name": self.name,
                "type": self.campaign_type, "status": self.status,
                "platforms": self.platforms, "budget": self.budget,
                "spent": self.spent, "revenue": self.revenue,
                "roi": self.get_roi()}


class CampaignManager:
    """Manage marketing, sponsorship, and cross-platform campaigns."""

    def __init__(self) -> None:
        self._campaigns: List[Campaign] = []
        self._campaign_index: Dict[str, Campaign] = {}

    def create(self, name: str, campaign_type: str = "marketing",
               platforms: Optional[List[str]] = None,
               budget: float = 0.0) -> Campaign:
        campaign = Campaign(name, campaign_type)
        if platforms:
            campaign.platforms = list(platforms)
        campaign.budget = budget
        self._campaigns.append(campaign)
        self._campaign_index[campaign.campaign_id] = campaign
        return campaign

    def get(self, campaign_id: str) -> Optional[Campaign]:
        return self._campaign_index.get(campaign_id)

    def update_status(self, campaign_id: str, status: str) -> bool:
        campaign = self.get(campaign_id)
        if campaign is None:
            return False
        if status in CAMPAIGN_STATUSES:
            campaign.status = status
            return True
        return False

    def record_spend(self, campaign_id: str, amount: float) -> bool:
        campaign = self.get(campaign_id)
        if campaign is None or amount < 0:
            return False
        campaign.spent += amount
        return True

    def record_revenue(self, campaign_id: str, amount: float) -> bool:
        campaign = self.get(campaign_id)
        if campaign is None or amount < 0:
            return False
        campaign.revenue += amount
        return True

    def get_active(self) -> List[Campaign]:
        return [c for c in self._campaigns if c.status == "active"]

    def get_by_type(self, campaign_type: str) -> List[Campaign]:
        return [c for c in self._campaigns if c.campaign_type == campaign_type]

    def get_by_platform(self, platform: str) -> List[Campaign]:
        return [c for c in self._campaigns if platform in c.platforms]

    def get_top_performing(self, count: int = 5) -> List[Campaign]:
        return sorted(self._campaigns, key=lambda c: c.get_roi(), reverse=True)[:count]

    def get_total_budget(self) -> float:
        return round(sum(c.budget for c in self._campaigns), 2)

    def get_total_spent(self) -> float:
        return round(sum(c.spent for c in self._campaigns), 2)

    def get_total_revenue(self) -> float:
        return round(sum(c.revenue for c in self._campaigns), 2)

    def get_stats(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        types: Dict[str, int] = {}
        for c in self._campaigns:
            statuses[c.status] = statuses.get(c.status, 0) + 1
            types[c.campaign_type] = types.get(c.campaign_type, 0) + 1
        return {"total": len(self._campaigns), "by_status": statuses,
                "by_type": types, "total_budget": self.get_total_budget(),
                "total_spent": self.get_total_spent()}
