"""CampaignManager — Manage Pinterest campaigns, seasonal campaigns, product launches."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.traffic_manager.models.traffic_models import Campaign, CampaignStatus, TrafficSourceType
from layers.layer23_website_manager.traffic_manager.exceptions import CampaignError


class CampaignManager:
    """Create, manage, and analyze traffic campaigns."""

    def __init__(self) -> None:
        self._campaigns: Dict[str, Campaign] = {}
        self._lock = threading.Lock()

    def create_campaign(self, name: str, campaign_type: str = "seasonal",
                         source_type: TrafficSourceType = TrafficSourceType.PINTEREST,
                         niche: str = "", budget: float = 0.0) -> Campaign:
        campaign = Campaign(name=name, campaign_type=campaign_type,
                             source_type=source_type, niche=niche, budget=budget,
                             status=CampaignStatus.DRAFT)
        with self._lock: self._campaigns[campaign.campaign_id] = campaign
        return campaign

    def start_campaign(self, campaign_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if not c: return False
        c.status = CampaignStatus.ACTIVE; c.start_date = time.time(); return True

    def pause_campaign(self, campaign_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if not c: return False
        c.status = CampaignStatus.PAUSED; return True

    def complete_campaign(self, campaign_id: str) -> bool:
        c = self._campaigns.get(campaign_id)
        if not c: return False
        c.status = CampaignStatus.COMPLETED; c.end_date = time.time(); return True

    def record_metric(self, campaign_id: str, clicks: int = 0,
                       impressions: int = 0, conversions: int = 0, spent: float = 0.0) -> bool:
        c = self._campaigns.get(campaign_id)
        if not c: return False
        with self._lock:
            c.clicks += clicks; c.impressions += impressions
            c.conversions += conversions; c.spent += spent
        return True

    def get_active_campaigns(self) -> List[Campaign]:
        return [c for c in self._campaigns.values() if c.status == CampaignStatus.ACTIVE]

    def get_campaign_by_niche(self, niche: str) -> List[Campaign]:
        return [c for c in self._campaigns.values() if c.niche == niche]

    def get_stats(self) -> Dict[str, Any]:
        active = len(self.get_active_campaigns())
        return {"total_campaigns": len(self._campaigns), "active": active,
                "total_spent": sum(c.spent for c in self._campaigns.values()),
                "total_clicks": sum(c.clicks for c in self._campaigns.values())}
