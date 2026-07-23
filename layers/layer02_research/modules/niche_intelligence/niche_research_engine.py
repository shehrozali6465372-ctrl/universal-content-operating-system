"""NicheResearchEngine — Deep market research: size, competition, keywords, trends."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class NicheProfile:
    __slots__ = ("name", "category", "market_size_usd", "growth_rate", "competition_level",
                 "difficulty_score", "opportunity_score", "keywords", "trends",
                 "sub_niches", "audience_size", "avg_cpc", "monetization_potential",
                 "last_researched", "data_sources")

    def __init__(self, name: str, category: str = "") -> None:
        self.name = name
        self.category = category
        self.market_size_usd = 0.0
        self.growth_rate = 0.0
        self.competition_level = "medium"
        self.difficulty_score = 50.0
        self.opportunity_score = 0.0
        self.keywords: List[Dict[str, Any]] = []
        self.trends: List[Dict[str, Any]] = []
        self.sub_niches: List[str] = []
        self.audience_size = 0
        self.avg_cpc = 0.0
        self.monetization_potential = "medium"
        self.last_researched = 0.0
        self.data_sources: List[str] = []

    @property
    def score(self) -> float:
        size_score = min(self.market_size_usd / 1_000_000_000, 1.0) * 25
        growth_score = min(max(self.growth_rate, 0) / 50, 1.0) * 20
        opp_score = min(self.opportunity_score / 100, 1.0) * 25
        competition_bonus = {"low": 15, "medium": 8, "high": 2}.get(self.competition_level, 5)
        potential_bonus = {"very_high": 15, "high": 12, "medium": 8, "low": 3}.get(
            self.monetization_potential, 5
        )
        return size_score + growth_score + opp_score + competition_bonus + potential_bonus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "category": self.category,
            "market_size_usd": self.market_size_usd,
            "growth_rate": self.growth_rate,
            "competition_level": self.competition_level,
            "difficulty_score": round(self.difficulty_score, 1),
            "opportunity_score": round(self.opportunity_score, 1),
            "overall_score": round(self.score, 1),
            "sub_niches": self.sub_niches,
            "audience_size": self.audience_size,
            "avg_cpc": round(self.avg_cpc, 2),
            "monetization_potential": self.monetization_potential,
            "keywords_count": len(self.keywords),
            "trends_count": len(self.trends),
            "last_researched": self.last_researched,
        }


class TrendData:
    __slots__ = ("keyword", "source", "interest_score", "direction",
                 "data_points", "seasonality", "peak_months", "last_updated")

    def __init__(self, keyword: str, source: str = "google_trends") -> None:
        self.keyword = keyword
        self.source = source
        self.interest_score = 0.0
        self.direction = "stable"
        self.data_points: List[Dict[str, Any]] = []
        self.seasonality = False
        self.peak_months: List[int] = []
        self.last_updated = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword, "source": self.source,
            "interest_score": round(self.interest_score, 1),
            "direction": self.direction, "seasonality": self.seasonality,
            "peak_months": self.peak_months,
        }


class NicheResearchEngine:
    """Researches and profiles niches with market data, trends, and competition."""
    _instance: Optional["NicheResearchEngine"] = None
    _lock = threading.Lock()

    DEFAULT_NICHES = [
        {"name": "Technology & Gadgets", "category": "tech", "market_usd": 5_000_000_000,
         "growth": 12.5, "competition": "high", "audience": 500_000_000, "cpc": 1.50},
        {"name": "Health & Fitness", "category": "health", "market_usd": 4_500_000_000,
         "growth": 8.2, "competition": "high", "audience": 400_000_000, "cpc": 2.00},
        {"name": "Personal Finance", "category": "finance", "market_usd": 8_000_000_000,
         "growth": 15.0, "competition": "high", "audience": 600_000_000, "cpc": 3.50},
        {"name": "Cryptocurrency", "category": "crypto", "market_usd": 3_000_000_000,
         "growth": 25.0, "competition": "medium", "audience": 300_000_000, "cpc": 2.80},
        {"name": "Home & Kitchen", "category": "home", "market_usd": 6_000_000_000,
         "growth": 6.5, "competition": "medium", "audience": 350_000_000, "cpc": 1.20},
        {"name": "Fashion & Beauty", "category": "fashion", "market_usd": 7_000_000_000,
         "growth": 9.0, "competition": "high", "audience": 450_000_000, "cpc": 1.80},
        {"name": "Online Education", "category": "education", "market_usd": 4_000_000_000,
         "growth": 18.0, "competition": "medium", "audience": 250_000_000, "cpc": 2.20},
        {"name": "SaaS & Software", "category": "saas", "market_usd": 5_500_000_000,
         "growth": 20.0, "competition": "medium", "audience": 200_000_000, "cpc": 4.00},
        {"name": "Travel & Tourism", "category": "travel", "market_usd": 9_000_000_000,
         "growth": 7.0, "competition": "high", "audience": 500_000_000, "cpc": 1.60},
        {"name": "Gaming", "category": "gaming", "market_usd": 6_500_000_000,
         "growth": 13.0, "competition": "medium", "audience": 400_000_000, "cpc": 1.00},
    ]

    def __new__(cls) -> "NicheResearchEngine":
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
        self._niches: Dict[str, NicheProfile] = {}
        self._trends: Dict[str, List[TrendData]] = {}
        self._research_history: List[Dict[str, Any]] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        for d in self.DEFAULT_NICHES:
            np = NicheProfile(d["name"], d["category"])
            np.market_size_usd = d["market_usd"]
            np.growth_rate = d["growth"]
            np.competition_level = d["competition"]
            np.audience_size = d["audience"]
            np.avg_cpc = d["cpc"]
            np.opportunity_score = self._calc_opportunity(np)
            np.monetization_potential = self._calc_monetization_potential(np)
            self._niches[d["category"]] = np

    def _calc_opportunity(self, np: NicheProfile) -> float:
        growth_factor = min(np.growth_rate / 30, 1.0) * 40
        competition_factor = {"low": 30, "medium": 15, "high": 5}.get(np.competition_level, 10)
        cpc_factor = min(np.avg_cpc / 5, 1.0) * 15
        market_factor = min(np.market_size_usd / 10_000_000_000, 1.0) * 15
        return growth_factor + competition_factor + cpc_factor + market_factor

    def _calc_monetization_potential(self, np: NicheProfile) -> str:
        s = self._calc_opportunity(np)
        if s >= 65:
            return "very_high"
        elif s >= 45:
            return "high"
        elif s >= 25:
            return "medium"
        return "low"

    def add_niche(self, name: str, category: str, market_size: float = 0.0,
                  growth_rate: float = 0.0, competition: str = "medium",
                  audience: int = 0, cpc: float = 0.0,
                  sub_niches: List[str] = None) -> NicheProfile:
        np = NicheProfile(name, category)
        np.market_size_usd = market_size
        np.growth_rate = growth_rate
        np.competition_level = competition
        np.audience_size = audience
        np.avg_cpc = cpc
        np.sub_niches = sub_niches or []
        np.opportunity_score = self._calc_opportunity(np)
        np.monetization_potential = self._calc_monetization_potential(np)
        np.last_researched = time.time()
        self._niches[category] = np
        return np

    def get_niche(self, category: str) -> Optional[NicheProfile]:
        return self._niches.get(category)

    def list_niches(self) -> List[NicheProfile]:
        return sorted(self._niches.values(), key=lambda n: n.score, reverse=True)

    def add_keywords(self, category: str, keywords: List[Dict[str, Any]]) -> bool:
        np = self._niches.get(category)
        if not np:
            return False
        np.keywords.extend(keywords)
        return True

    def add_trend(self, category: str, keyword: str, interest: float = 0.0,
                  direction: str = "stable", source: str = "google_trends") -> TrendData:
        trend = TrendData(keyword, source)
        trend.interest_score = interest
        trend.direction = direction
        self._trends.setdefault(category, []).append(trend)
        np = self._niches.get(category)
        if np:
            np.trends.append(trend.to_dict())
        return trend

    def get_niche_trends(self, category: str) -> List[TrendData]:
        return self._trends.get(category, [])

    def get_top_niches(self, limit: int = 10) -> List[NicheProfile]:
        return self.list_niches()[:limit]

    def get_niche_by_score(self, min_score: float = 50.0) -> List[NicheProfile]:
        return [n for n in self._niches.values() if n.score >= min_score]

    def get_research_report(self) -> Dict[str, Any]:
        niches = self.list_niches()
        return {
            "total_niches": len(niches),
            "niches": {n.category: n.to_dict() for n in niches},
            "top_3": [n.to_dict() for n in niches[:3]],
            "avg_score": round(
                sum(n.score for n in niches) / len(niches), 1
            ) if niches else 0,
            "very_high_potential": sum(
                1 for n in niches if n.monetization_potential == "very_high"
            ),
            "total_keywords": sum(len(n.keywords) for n in niches),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "niches": len(self._niches),
            "trends": sum(len(t) for t in self._trends.values()),
            "research_history": len(self._research_history),
        }


def get_niche_research_engine() -> NicheResearchEngine:
    return NicheResearchEngine()
