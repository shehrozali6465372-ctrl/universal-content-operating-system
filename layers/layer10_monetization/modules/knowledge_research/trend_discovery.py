"""TrendDiscovery — Find trending topics and viral patterns."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_TD_COUNTER = itertools.count(1)


class Trend:
    """A discovered trend."""

    __slots__ = ("trend_id", "topic", "platform", "trend_score",
                 "growth_rate", "confidence", "category", "discovered_at")

    def __init__(self, topic: str = "", platform: str = "universal") -> None:
        self.trend_id: str = f"trend_{next(_TD_COUNTER)}"
        self.topic = topic
        self.platform = platform
        self.trend_score: float = 0.0
        self.growth_rate: float = 0.0
        self.confidence: float = 0.5
        self.category: str = ""
        self.discovered_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"trend_id": self.trend_id, "topic": self.topic,
                "platform": self.platform, "score": round(self.trend_score, 3),
                "growth": round(self.growth_rate, 3), "confidence": round(self.confidence, 3)}


TREND_CATEGORIES = ("topic", "hashtag", "keyword", "format", "seasonal", "emerging", "competitor")


class TrendDiscovery:
    """Discover trending topics, hashtags, and viral patterns."""

    def __init__(self) -> None:
        self._trends: List[Trend] = []
        self._trend_history: List[Dict[str, Any]] = []

    def discover(self, topic: str = "", platform: str = "universal",
                 category: str = "topic") -> List[Trend]:
        detected = []
        trend = Trend(topic or f"trending_{platform}", platform)
        trend.trend_score = min(1.0, 0.3 + hash(topic) % 70 / 100)
        trend.growth_rate = min(5.0, trend.trend_score * 3)
        trend.confidence = min(0.95, 0.4 + trend.trend_score * 0.5)
        trend.category = category if category in TREND_CATEGORIES else "topic"
        self._trends.append(trend)
        detected.append(trend)
        return detected

    def discover_batch(self, topics: List[str], platform: str = "universal") -> List[Trend]:
        results = []
        for topic in topics:
            results.extend(self.discover(topic, platform))
        return results

    def get_top_trends(self, count: int = 10, platform: str = "") -> List[Trend]:
        trends = self._trends
        if platform:
            trends = [t for t in trends if t.platform == platform]
        return sorted(trends, key=lambda t: t.trend_score, reverse=True)[:count]

    def get_by_category(self, category: str) -> List[Trend]:
        return [t for t in self._trends if t.category == category]

    def get_stats(self) -> Dict[str, Any]:
        platforms = {}
        for t in self._trends:
            platforms[t.platform] = platforms.get(t.platform, 0) + 1
        return {"total": len(self._trends), "by_platform": platforms}
