"""CompetitorIntelligence — Analyzes competitors: content, monetization, social strategy."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class CompetitorProfile:
    __slots__ = ("id", "name", "domain", "niche", "monthly_traffic", "domain_authority",
                 "backlinks", "content_count", "avg_engagement", "social_followers",
                 "monetization_methods", "affiliate_programs", "content_strategy",
                 "strengths", "weaknesses", "threat_level", "last_analyzed", "score")

    def __init__(self, name: str, domain: str = "", niche: str = "") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.domain = domain
        self.niche = niche
        self.monthly_traffic = 0
        self.domain_authority = 0
        self.backlinks = 0
        self.content_count = 0
        self.avg_engagement = 0.0
        self.social_followers: Dict[str, int] = {}
        self.monetization_methods: List[str] = []
        self.affiliate_programs: List[str] = []
        self.content_strategy: Dict[str, Any] = {}
        self.strengths: List[str] = []
        self.weaknesses: List[str] = []
        self.threat_level = "medium"
        self.last_analyzed = 0.0
        self.score = 0.0

    @property
    def total_social_followers(self) -> int:
        return sum(self.social_followers.values())

    @property
    def estimated_monthly_revenue(self) -> float:
        rpm = 10.0
        return self.monthly_traffic * (rpm / 1000)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "domain": self.domain,
            "niche": self.niche, "monthly_traffic": self.monthly_traffic,
            "domain_authority": self.domain_authority, "backlinks": self.backlinks,
            "content_count": self.content_count,
            "total_social_followers": self.total_social_followers,
            "monetization_methods": self.monetization_methods,
            "affiliate_programs": self.affiliate_programs,
            "strengths": self.strengths, "weaknesses": self.weaknesses,
            "threat_level": self.threat_level,
            "estimated_revenue": round(self.estimated_monthly_revenue, 2),
            "score": round(self.score, 1),
        }


class CompetitorIntelligence:
    """Discovers and analyzes competitors in each niche."""
    _instance: Optional["CompetitorIntelligence"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CompetitorIntelligence":
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
        self._competitors: Dict[str, CompetitorProfile] = {}
        self._niche_index: Dict[str, List[str]] = {}
        self._analysis_history: List[Dict[str, Any]] = []

    def add_competitor(self, name: str, domain: str = "", niche: str = "",
                       traffic: int = 0, da: int = 0, backlinks: int = 0,
                       content_count: int = 0, monetization: List[str] = None,
                       programs: List[str] = None,
                       strengths: List[str] = None, weaknesses: List[str] = None,
                       threat: str = "medium") -> CompetitorProfile:
        c = CompetitorProfile(name, domain, niche)
        c.monthly_traffic = traffic
        c.domain_authority = da
        c.backlinks = backlinks
        c.content_count = content_count
        c.monetization_methods = monetization or []
        c.affiliate_programs = programs or []
        c.strengths = strengths or []
        c.weaknesses = weaknesses or []
        c.threat_level = threat
        c.last_analyzed = time.time()
        c.score = self._score_competitor(c)
        self._competitors[c.id] = c
        if niche:
            self._niche_index.setdefault(niche, []).append(c.id)
        return c

    def _score_competitor(self, c: CompetitorProfile) -> float:
        traffic_score = min(c.monthly_traffic / 1_000_000, 1.0) * 30
        da_score = (c.domain_authority / 100) * 25
        backlink_score = min(c.backlinks / 100_000, 1.0) * 15
        content_score = min(c.content_count / 1000, 1.0) * 15
        social_score = min(c.total_social_followers / 100_000, 1.0) * 15
        return traffic_score + da_score + backlink_score + content_score + social_score

    def get_competitor(self, cid: str) -> Optional[CompetitorProfile]:
        return self._competitors.get(cid)

    def get_by_niche(self, niche: str) -> List[CompetitorProfile]:
        ids = self._niche_index.get(niche, [])
        return sorted(
            [self._competitors[i] for i in ids if i in self._competitors],
            key=lambda c: c.score, reverse=True,
        )

    def get_top_competitors(self, limit: int = 10) -> List[CompetitorProfile]:
        return sorted(self._competitors.values(), key=lambda c: c.score, reverse=True)[:limit]

    def get_high_threat(self) -> List[CompetitorProfile]:
        return [c for c in self._competitors.values() if c.threat_level == "high"]

    def get_monetization_overlap(self, program: str) -> List[CompetitorProfile]:
        return [c for c in self._competitors.values() if program in c.affiliate_programs]

    def analyze_gaps(self, niche: str) -> Dict[str, Any]:
        comps = self.get_by_niche(niche)
        all_strengths = []
        all_weaknesses = []
        all_monetization = set()
        for c in comps:
            all_strengths.extend(c.strengths)
            all_weaknesses.extend(c.weaknesses)
            all_monetization.update(c.monetization_methods)
        strength_freq = {}
        for s in all_strengths:
            strength_freq[s] = strength_freq.get(s, 0) + 1
        weakness_freq = {}
        for w in all_weaknesses:
            weakness_freq[w] = weakness_freq.get(w, 0) + 1
        return {
            "niche": niche,
            "competitors": len(comps),
            "avg_traffic": round(
                sum(c.monthly_traffic for c in comps) / len(comps), 0
            ) if comps else 0,
            "avg_da": round(
                sum(c.domain_authority for c in comps) / len(comps), 1
            ) if comps else 0,
            "common_strengths": strength_freq,
            "common_weaknesses": weakness_freq,
            "monetization_methods": list(all_monetization),
            "gaps": [w for w, count in weakness_freq.items() if count >= 2],
        }

    def get_intelligence_report(self) -> Dict[str, Any]:
        comps = list(self._competitors.values())
        return {
            "total_competitors": len(comps),
            "by_niche": {n: len(ids) for n, ids in self._niche_index.items()},
            "high_threat": len([c for c in comps if c.threat_level == "high"]),
            "avg_traffic": round(
                sum(c.monthly_traffic for c in comps) / len(comps), 0
            ) if comps else 0,
            "avg_da": round(
                sum(c.domain_authority for c in comps) / len(comps), 1
            ) if comps else 0,
            "total_content": sum(c.content_count for c in comps),
            "top_competitors": [c.to_dict() for c in self.get_top_competitors(5)],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "competitors": len(self._competitors),
            "niches": len(self._niche_index),
            "analyses": len(self._analysis_history),
        }


def get_competitor_intelligence() -> CompetitorIntelligence:
    return CompetitorIntelligence()
