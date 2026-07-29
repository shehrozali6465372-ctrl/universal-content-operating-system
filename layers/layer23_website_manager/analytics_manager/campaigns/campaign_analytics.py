"""CampaignAnalytics — Track campaign performance, ROI, CTR, conversion, revenue."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import CampaignAnalyticsData


class CampaignAnalytics:
    def __init__(self):
        self._campaigns: Dict[str, CampaignAnalyticsData] = {}
        self._lock = threading.Lock()

    def record_campaign(self, campaign_id: str, name: str = "", impressions: int = 0,
                         clicks: int = 0, conversions: int = 0, spent: float = 0.0, revenue: float = 0.0):
        with self._lock:
            if campaign_id not in self._campaigns:
                self._campaigns[campaign_id] = CampaignAnalyticsData(campaign_id=campaign_id, name=name)
            c = self._campaigns[campaign_id]
            c.impressions += impressions; c.clicks += clicks; c.conversions += conversions
            c.spent += spent; c.revenue += revenue
            c.roi = ((revenue - spent) / max(spent, 1)) * 100

    def get_best_campaigns(self, top_k: int = 5) -> List[CampaignAnalyticsData]:
        return sorted(self._campaigns.values(), key=lambda c: c.roi, reverse=True)[:top_k]

    def get_summary(self) -> Dict[str, Any]:
        cs = list(self._campaigns.values())
        return {"total_campaigns": len(cs), "total_clicks": sum(c.clicks for c in cs),
                "total_conversions": sum(c.conversions for c in cs),
                "total_spent": round(sum(c.spent for c in cs), 2),
                "total_revenue": round(sum(c.revenue for c in cs), 2),
                "avg_roi": round(sum(c.roi for c in cs) / max(len(cs), 1), 1)}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_campaigns": s["total_campaigns"]}
