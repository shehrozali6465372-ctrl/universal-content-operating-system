"""Niche Intelligence Engine — Phase 9."""
from .niche_intelligence_manager import NicheIntelligenceManager, get_niche_intelligence
from .niche_research_engine import NicheResearchEngine, get_niche_research_engine
from .product_intelligence import ProductIntelligence, get_product_intelligence
from .keyword_intelligence import KeywordIntelligence, get_keyword_intelligence
from .competitor_intelligence import CompetitorIntelligence, get_competitor_intelligence
from .content_opportunity_finder import ContentOpportunityFinder, get_content_opportunity_finder
from .revenue_prediction_engine import RevenuePredictionEngine, get_revenue_prediction_engine

__all__ = [
    "NicheIntelligenceManager", "get_niche_intelligence",
    "NicheResearchEngine", "get_niche_research_engine",
    "ProductIntelligence", "get_product_intelligence",
    "KeywordIntelligence", "get_keyword_intelligence",
    "CompetitorIntelligence", "get_competitor_intelligence",
    "ContentOpportunityFinder", "get_content_opportunity_finder",
    "RevenuePredictionEngine", "get_revenue_prediction_engine",
]
