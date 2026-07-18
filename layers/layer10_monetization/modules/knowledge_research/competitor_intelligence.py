"""CompetitorIntelligence — Analyze competitor strategies."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_CI_COUNTER = itertools.count(1)


class CompetitorProfile:
    """A competitor's profile."""

    __slots__ = ("profile_id", "name", "platform", "posting_frequency",
                 "content_types", "engagement_rate", "top_hooks", "top_ctas",
                 "updated_at")

    def __init__(self, name: str = "", platform: str = "") -> None:
        self.profile_id: str = f"comp_{next(_CI_COUNTER)}"
        self.name = name
        self.platform = platform
        self.posting_frequency: float = 0.0
        self.content_types: List[str] = []
        self.engagement_rate: float = 0.0
        self.top_hooks: List[str] = []
        self.top_ctas: List[str] = []
        self.updated_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"profile_id": self.profile_id, "name": self.name,
                "platform": self.platform, "engagement_rate": round(self.engagement_rate, 3)}


class CompetitorIntelligence:
    """Analyze and track competitor strategies."""

    def __init__(self) -> None:
        self._competitors: List[CompetitorProfile] = []
        self._analyses: List[Dict[str, Any]] = []

    def add_competitor(self, name: str, platform: str = "") -> CompetitorProfile:
        profile = CompetitorProfile(name, platform)
        self._competitors.append(profile)
        return profile

    def analyze(self, competitor_id: str, data: Optional[Dict[str, Any]] = None) -> Optional[CompetitorProfile]:
        for comp in self._competitors:
            if comp.profile_id == competitor_id:
                if data:
                    comp.posting_frequency = data.get("posting_frequency", comp.posting_frequency)
                    comp.engagement_rate = data.get("engagement_rate", comp.engagement_rate)
                    comp.content_types = data.get("content_types", comp.content_types)
                    comp.updated_at = time.time()
                self._analyses.append({"competitor_id": competitor_id, "data": data or {}})
                return comp
        return None

    def get_competitor(self, competitor_id: str) -> Optional[CompetitorProfile]:
        for c in self._competitors:
            if c.profile_id == competitor_id:
                return c
        return None

    def get_by_platform(self, platform: str) -> List[CompetitorProfile]:
        return [c for c in self._competitors if c.platform == platform]

    def compare(self) -> List[Dict[str, Any]]:
        return [{"name": c.name, "platform": c.platform,
                 "engagement": c.engagement_rate} for c in self._competitors]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_competitors": len(self._competitors),
                "total_analyses": len(self._analyses)}
