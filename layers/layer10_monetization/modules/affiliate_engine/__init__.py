"""Affiliate & Monetization Engine — Phase 8."""
from .affiliate_engine_manager import AffiliateEngineManager, get_affiliate_engine
from .affiliate_manager import AffiliateManager, AffiliateProgram, AffiliateLink, get_affiliate_manager
from .link_intelligence import LinkIntelligence, TrackedLink, get_link_intelligence
from .revenue_analytics import RevenueAnalytics, PostRevenue, get_revenue_analytics
from .campaign_manager import CampaignManager, Campaign, get_campaign_manager
from .ai_monetization_optimizer import AIMonetizationOptimizer, get_monetization_optimizer

__all__ = [
    "AffiliateEngineManager", "get_affiliate_engine",
    "AffiliateManager", "get_affiliate_manager",
    "LinkIntelligence", "get_link_intelligence",
    "RevenueAnalytics", "get_revenue_analytics",
    "CampaignManager", "get_campaign_manager",
    "AIMonetizationOptimizer", "get_monetization_optimizer",
]
