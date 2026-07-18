"""MarketIntelligence — Track market trends and opportunities."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_MI_COUNTER = itertools.count(1)


class MarketInsight:
    """A market intelligence insight."""

    __slots__ = ("insight_id", "category", "description", "impact",
                 "confidence", "platform", "detected_at")

    def __init__(self, category: str = "", description: str = "") -> None:
        self.insight_id: str = f"mins_{next(_MI_COUNTER)}"
        self.category = category
        self.description = description
        self.impact: float = 0.5
        self.confidence: float = 0.5
        self.platform: str = "universal"
        self.detected_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"insight_id": self.insight_id, "category": self.category,
                "impact": round(self.impact, 3), "confidence": round(self.confidence, 3)}


class MarketIntelligence:
    """Track industry, niche growth, opportunities, and risks."""

    def __init__(self) -> None:
        self._insights: List[MarketInsight] = []

    def analyze(self, category: str = "industry",
                platform: str = "universal") -> MarketInsight:
        insight = MarketInsight(category, f"Analysis for {category} on {platform}")
        insight.platform = platform
        insight.impact = 0.6
        insight.confidence = 0.7
        self._insights.append(insight)
        return insight

    def get_by_category(self, category: str) -> List[MarketInsight]:
        return [i for i in self._insights if i.category == category]

    def get_by_platform(self, platform: str) -> List[MarketInsight]:
        return [i for i in self._insights if i.platform == platform]

    def get_top_insights(self, count: int = 5) -> List[MarketInsight]:
        return sorted(self._insights, key=lambda i: i.impact, reverse=True)[:count]

    def get_stats(self) -> Dict[str, Any]:
        cats = {}
        for i in self._insights:
            cats[i.category] = cats.get(i.category, 0) + 1
        return {"total": len(self._insights), "by_category": cats}
