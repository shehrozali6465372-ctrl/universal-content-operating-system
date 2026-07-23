"""AffiliateEngineManager — Integrates all affiliate & monetization modules."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .affiliate_manager import AffiliateManager, get_affiliate_manager
from .link_intelligence import LinkIntelligence, get_link_intelligence
from .revenue_analytics import RevenueAnalytics, get_revenue_analytics
from .campaign_manager import CampaignManager, get_campaign_manager
from .ai_monetization_optimizer import AIMonetizationOptimizer, get_monetization_optimizer


class AffiliateEngineManager:
    """Master integrator for the Affiliate & Monetization Engine."""
    _instance: Optional["AffiliateEngineManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AffiliateEngineManager":
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
        self._affiliate = get_affiliate_manager()
        self._links = get_link_intelligence()
        self._revenue = get_revenue_analytics()
        self._campaigns = get_campaign_manager()
        self._optimizer = get_monetization_optimizer()
        self._initialized_at = time.time()

    @property
    def affiliate(self) -> AffiliateManager:
        return self._affiliate

    @property
    def links(self) -> LinkIntelligence:
        return self._links

    @property
    def revenue(self) -> RevenueAnalytics:
        return self._revenue

    @property
    def campaigns(self) -> CampaignManager:
        return self._campaigns

    @property
    def optimizer(self) -> AIMonetizationOptimizer:
        return self._optimizer

    def create_niche_campaign(self, name: str, niche: str, budget: float = 0.0,
                              target_revenue: float = 0.0, platforms: List[str] = None) -> Dict[str, Any]:
        camp = self._campaigns.create_campaign(
            name, niche, budget, target_revenue, platforms=platforms,
        )
        best_program = self._find_best_program_for_niche(niche)
        return {
            "campaign": camp.to_dict(),
            "recommended_program": best_program,
        }

    def _find_best_program_for_niche(self, niche: str) -> Optional[Dict[str, Any]]:
        programs = self._affiliate.list_programs()
        niche_lower = niche.lower()
        best = None
        best_score = -1
        for p in programs:
            score = 0
            if niche_lower in [c.lower() for c in p.categories]:
                score += 50
            score += p.commission_rate
            if p.epc > 0:
                score += p.epc * 100
            if score > best_score:
                best_score = score
                best = p
        return best.to_dict() if best else None

    def track_click(self, link_id: str, post_id: str = "", source: str = "",
                    platform: str = "", niche: str = "", campaign_id: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {"link_id": link_id}

        tracked = self._links.resolve_link(
            self._links.get_link(link_id).short_slug
            if self._links.get_link(link_id) else link_id
        )
        result["resolved_url"] = tracked

        rev_evt = self._revenue.record_click(post_id, link_id=link_id, niche=niche, platform=platform)
        result["revenue_event"] = rev_evt.id

        if campaign_id:
            self._campaigns.record_click(campaign_id)

        return result

    def track_conversion(self, post_id: str, revenue: float, commission: float = 0.0,
                         niche: str = "", platform: str = "", campaign_id: str = "",
                         link_id: str = "") -> Dict[str, Any]:
        rev_evt = self._revenue.record_conversion(
            post_id, revenue, commission, link_id=link_id, niche=niche, platform=platform,
        )
        if campaign_id:
            self._campaigns.record_conversion(campaign_id, revenue)

        return {"revenue_event": rev_evt.to_dict()}

    def get_full_status(self) -> Dict[str, Any]:
        return {
            "overall": "Active",
            "initialized": True,
            "uptime_seconds": round(time.time() - self._initialized_at, 2),
            "affiliate": self._affiliate.get_revenue_summary(),
            "links": self._links.get_link_stats(),
            "revenue": self._revenue.get_analytics_summary(),
            "campaigns": self._campaigns.get_campaign_status(),
            "optimizer": self._optimizer.get_optimization_report(),
        }

    def get_executive_summary(self) -> Dict[str, Any]:
        aff = self._affiliate.get_revenue_summary()
        rev = self._revenue.get_analytics_summary()
        camp = self._campaigns.get_campaign_status()
        opt = self._optimizer.get_optimization_report()
        return {
            "total_programs": aff["total_programs"],
            "total_links": aff["total_links"],
            "total_campaigns": camp["total_campaigns"],
            "active_campaigns": camp["active"],
            "total_revenue": rev["total_revenue"],
            "total_clicks": rev["total_clicks"],
            "total_conversions": rev["total_conversions"],
            "overall_conversion_rate": rev["overall_conversion_rate"],
            "overall_epc": rev["overall_epc"],
            "top_niches": opt.get("top_niches", []),
            "recommendations": opt.get("total_recommendations", 0),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "affiliate": self._affiliate.stats(),
            "links": self._links.get_link_stats(),
            "revenue": self._revenue.stats(),
            "campaigns": self._campaigns.stats(),
            "optimizer": self._optimizer.stats(),
        }


def get_affiliate_engine() -> AffiliateEngineManager:
    return AffiliateEngineManager()
