"""NicheIntelligenceManager — Master integrator for all 7 niche intelligence modules."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .niche_research_engine import NicheResearchEngine, NicheProfile, get_niche_research_engine
from .product_intelligence import ProductIntelligence, ProductProfile, get_product_intelligence
from .keyword_intelligence import KeywordIntelligence, KeywordEntry, get_keyword_intelligence
from .competitor_intelligence import CompetitorIntelligence, CompetitorProfile, get_competitor_intelligence
from .content_opportunity_finder import ContentOpportunityFinder, ContentOpportunity, get_content_opportunity_finder
from .revenue_prediction_engine import RevenuePredictionEngine, get_revenue_prediction_engine


class NicheIntelligenceManager:
    """Master integrator for all niche intelligence modules."""
    _instance: Optional["NicheIntelligenceManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "NicheIntelligenceManager":
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
        self._research = get_niche_research_engine()
        self._products = get_product_intelligence()
        self._keywords = get_keyword_intelligence()
        self._competitors = get_competitor_intelligence()
        self._opportunities = get_content_opportunity_finder()
        self._predictions = get_revenue_prediction_engine()
        self._initialized_at = time.time()

    @property
    def research(self) -> NicheResearchEngine:
        return self._research

    @property
    def products(self) -> ProductIntelligence:
        return self._products

    @property
    def keywords(self) -> KeywordIntelligence:
        return self._keywords

    @property
    def competitors(self) -> CompetitorIntelligence:
        return self._competitors

    @property
    def opportunities(self) -> ContentOpportunityFinder:
        return self._opportunities

    @property
    def predictions(self) -> RevenuePredictionEngine:
        return self._predictions

    def analyze_niche(self, category: str) -> Dict[str, Any]:
        profile = self._research.get_niche(category)
        keywords = self._keywords.get_by_niche(category)
        competitors = self._competitors.get_by_niche(category)
        products = self._products.get_by_category(category)
        opps = self._opportunities.get_by_niche(category)
        prediction = self._predictions.get_niche_prediction(category)
        return {
            "niche": profile.to_dict() if profile else {"name": category},
            "keywords": len(keywords),
            "competitors": len(competitors),
            "products": len(products),
            "opportunities": len(opps),
            "revenue_prediction": prediction.to_dict() if prediction else None,
        }

    def get_niche_rankings(self) -> List[Dict[str, Any]]:
        niches = self._research.list_niches()
        rankings = []
        for n in niches:
            prediction = self._predictions.get_niche_prediction(n.category)
            rankings.append({
                "niche": n.name,
                "category": n.category,
                "score": round(n.score, 1),
                "monetization_potential": n.monetization_potential,
                "predicted_monthly": round(
                    prediction.predicted_monthly_revenue, 2
                ) if prediction else 0,
                "keywords": len(self._keywords.get_by_niche(n.category)),
                "competitors": len(self._competitors.get_by_niche(n.category)),
            })
        return sorted(rankings, key=lambda r: r["score"], reverse=True)

    def get_quick_wins(self) -> Dict[str, Any]:
        opps = self._opportunities.get_quick_wins()
        return {
            "total_quick_wins": len(opps),
            "opportunities": [o.to_dict() for o in opps[:10]],
        }

    def get_full_intelligence(self) -> Dict[str, Any]:
        return {
            "overall": "Active",
            "uptime_seconds": round(time.time() - self._initialized_at, 2),
            "research": self._research.get_research_report(),
            "products": self._products.get_intelligence_report(),
            "keywords": self._keywords.get_keyword_report(),
            "competitors": self._competitors.get_intelligence_report(),
            "opportunities": self._opportunities.get_opportunity_report(),
            "predictions": self._predictions.get_prediction_report(),
            "rankings": self.get_niche_rankings(),
        }

    def get_executive_summary(self) -> Dict[str, Any]:
        research = self._research.get_research_report()
        products = self._products.get_intelligence_report()
        keywords = self._keywords.get_keyword_report()
        competitors = self._competitors.get_intelligence_report()
        predictions = self._predictions.get_total_predicted_revenue()
        return {
            "total_niches": research["total_niches"],
            "total_products": products["total_products"],
            "total_keywords": keywords["total_keywords"],
            "total_competitors": competitors["total_competitors"],
            "predicted_monthly_revenue": predictions["monthly"],
            "predicted_annual_revenue": predictions["annual"],
            "very_high_potential_niches": research["very_high_potential"],
            "avg_niche_score": research["avg_score"],
            "top_niches": [r["niche"] for r in self.get_niche_rankings()[:3]],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "research": self._research.stats(),
            "products": self._products.stats(),
            "keywords": self._keywords.stats(),
            "competitors": self._competitors.stats(),
            "opportunities": self._opportunities.stats(),
            "predictions": self._predictions.stats(),
        }


def get_niche_intelligence() -> NicheIntelligenceManager:
    return NicheIntelligenceManager()
