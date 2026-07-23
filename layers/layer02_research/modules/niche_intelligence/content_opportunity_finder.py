"""ContentOpportunityFinder — Finds best topics, platforms, and formats for content."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class ContentOpportunity:
    __slots__ = ("id", "topic", "niche", "platform", "format", "content_type",
                 "opportunity_score", "estimated_traffic", "estimated_revenue",
                 "competition_level", "difficulty", "keywords", "reason",
                 "created_at", "status")

    def __init__(self, topic: str, niche: str = "", platform: str = "blog",
                 content_type: str = "blog_post") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.topic = topic
        self.niche = niche
        self.platform = platform
        self.format = "article"
        self.content_type = content_type
        self.opportunity_score = 0.0
        self.estimated_traffic = 0
        self.estimated_revenue = 0.0
        self.competition_level = "medium"
        self.difficulty = 50.0
        self.keywords: List[str] = []
        self.reason = ""
        self.created_at = time.time()
        self.status = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "topic": self.topic, "niche": self.niche,
            "platform": self.platform, "format": self.format,
            "content_type": self.content_type,
            "opportunity_score": round(self.opportunity_score, 1),
            "estimated_traffic": self.estimated_traffic,
            "estimated_revenue": round(self.estimated_revenue, 2),
            "competition": self.competition_level,
            "difficulty": round(self.difficulty, 1),
            "keywords": self.keywords, "reason": self.reason,
            "status": self.status,
        }


PLATFORMS = ["blog", "facebook", "instagram", "x", "linkedin",
             "youtube", "tiktok", "pinterest", "wordpress", "medium"]

CONTENT_TYPES = {
    "blog": ["blog_post", "listicle", "review", "tutorial", "comparison", "guide"],
    "social": ["post", "thread", "reel", "story", "carousel", "video"],
    "video": ["tutorial", "review", "vlog", "short", "live"],
}


class ContentOpportunityFinder:
    """Discovers content opportunities across niches, platforms, and formats."""
    _instance: Optional["ContentOpportunityFinder"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ContentOpportunityFinder":
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
        self._opportunities: Dict[str, ContentOpportunity] = {}
        self._niche_index: Dict[str, List[str]] = {}
        self._platform_index: Dict[str, List[str]] = {}

    def find_opportunity(self, topic: str, niche: str = "", platform: str = "blog",
                         content_type: str = "blog_post", estimated_traffic: int = 0,
                         estimated_revenue: float = 0.0, competition: str = "medium",
                         difficulty: float = 50.0, keywords: List[str] = None,
                         reason: str = "") -> ContentOpportunity:
        opp = ContentOpportunity(topic, niche, platform, content_type)
        opp.estimated_traffic = estimated_traffic
        opp.estimated_revenue = estimated_revenue
        opp.competition_level = competition
        opp.difficulty = difficulty
        opp.keywords = keywords or []
        opp.reason = reason
        opp.opportunity_score = self._score_opportunity(opp)
        self._opportunities[opp.id] = opp
        if niche:
            self._niche_index.setdefault(niche, []).append(opp.id)
        self._platform_index.setdefault(platform, []).append(opp.id)
        return opp

    def _score_opportunity(self, o: ContentOpportunity) -> float:
        traffic_score = min(o.estimated_traffic / 100000, 1.0) * 30
        revenue_score = min(o.estimated_revenue / 500, 1.0) * 25
        diff_score = max(1 - (o.difficulty / 100), 0) * 25
        comp_bonus = {"low": 15, "medium": 8, "high": 3}.get(o.competition_level, 5)
        keyword_bonus = min(len(o.keywords) / 5, 1.0) * 5
        return traffic_score + revenue_score + diff_score + comp_bonus + keyword_bonus

    def get_opportunity(self, oid: str) -> Optional[ContentOpportunity]:
        return self._opportunities.get(oid)

    def get_by_niche(self, niche: str) -> List[ContentOpportunity]:
        ids = self._niche_index.get(niche, [])
        return sorted(
            [self._opportunities[i] for i in ids if i in self._opportunities],
            key=lambda o: o.opportunity_score, reverse=True,
        )

    def get_by_platform(self, platform: str) -> List[ContentOpportunity]:
        ids = self._platform_index.get(platform, [])
        return [self._opportunities[i] for i in ids if i in self._opportunities]

    def get_top_opportunities(self, limit: int = 10) -> List[ContentOpportunity]:
        return sorted(
            self._opportunities.values(),
            key=lambda o: o.opportunity_score, reverse=True,
        )[:limit]

    def get_quick_wins(self) -> List[ContentOpportunity]:
        return sorted(
            [o for o in self._opportunities.values()
             if o.opportunity_score >= 50 and o.difficulty <= 40],
            key=lambda o: o.opportunity_score, reverse=True,
        )

    def get_platform_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
        result: Dict[str, List[Dict[str, Any]]] = {}
        for platform, ids in self._platform_index.items():
            opps = [self._opportunities[i] for i in ids if i in self._opportunities]
            result[platform] = [
                {"topic": o.topic, "score": round(o.opportunity_score, 1)}
                for o in sorted(opps, key=lambda x: x.opportunity_score, reverse=True)[:5]
            ]
        return result

    def get_opportunity_report(self) -> Dict[str, Any]:
        opps = list(self._opportunities.values())
        return {
            "total_opportunities": len(opps),
            "by_niche": {n: len(ids) for n, ids in self._niche_index.items()},
            "by_platform": {p: len(ids) for p, ids in self._platform_index.items()},
            "quick_wins": len(self.get_quick_wins()),
            "avg_score": round(
                sum(o.opportunity_score for o in opps) / len(opps), 1
            ) if opps else 0,
            "total_estimated_traffic": sum(o.estimated_traffic for o in opps),
            "total_estimated_revenue": round(sum(o.estimated_revenue for o in opps), 2),
            "top_10": [o.to_dict() for o in self.get_top_opportunities(10)],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "opportunities": len(self._opportunities),
            "niches": len(self._niche_index),
            "platforms": len(self._platform_index),
        }


def get_content_opportunity_finder() -> ContentOpportunityFinder:
    return ContentOpportunityFinder()
