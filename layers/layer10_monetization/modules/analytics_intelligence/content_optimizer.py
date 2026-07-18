"""ContentOptimizer — Optimize content based on analytics insights."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_CO_COUNTER = itertools.count(1)


class ContentInsight:
    """An insight about content performance."""

    __slots__ = ("insight_id", "content_type", "metric", "value",
                 "recommendation", "priority", "platform", "created_at")

    def __init__(self, content_type: str = "", metric: str = "",
                 recommendation: str = "") -> None:
        self.insight_id: str = f"ci_{next(_CO_COUNTER)}"
        self.content_type = content_type
        self.metric = metric
        self.value: float = 0.0
        self.recommendation = recommendation
        self.priority: int = 1  # 1=high, 2=medium, 3=low
        self.platform: str = ""
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"insight_id": self.insight_id, "content_type": self.content_type,
                "metric": self.metric, "recommendation": self.recommendation,
                "priority": self.priority}


class ContentOptimizer:
    """Analyze content performance and generate optimization insights."""

    def __init__(self) -> None:
        self._insights: List[ContentInsight] = []
        self._content_scores: Dict[str, float] = {}

    def analyze_content(self, platform: str, content_type: str,
                        metrics: Dict[str, float]) -> List[ContentInsight]:
        insights: List[ContentInsight] = []
        engagement = metrics.get("engagement_rate", 0.0)
        ctr = metrics.get("ctr", 0.0)
        reach = metrics.get("reach", 0)

        if engagement < 0.02:
            insight = ContentInsight(content_type, "engagement_rate",
                                     "Improve hook and CTA for better engagement")
            insight.priority = 1
            insight.platform = platform
            insight.value = engagement
            insights.append(insight)

        if ctr < 0.01:
            insight = ContentInsight(content_type, "ctr",
                                     "Optimize title and preview for higher CTR")
            insight.priority = 2
            insight.platform = platform
            insight.value = ctr
            insights.append(insight)

        if reach > 0 and engagement > 0.05:
            insight = ContentInsight(content_type, "engagement_rate",
                                     "High engagement — increase posting frequency")
            insight.priority = 2
            insight.platform = platform
            insight.value = engagement
            insights.append(insight)

        self._insights.extend(insights)
        key = f"{platform}:{content_type}"
        self._content_scores[key] = engagement
        return insights

    def get_top_content_types(self, platform: str = "",
                              count: int = 5) -> List[Dict[str, Any]]:
        scores = []
        for key, score in self._content_scores.items():
            parts = key.split(":", 1)
            p, ct = parts[0], parts[1] if len(parts) > 1 else ""
            if platform and p != platform:
                continue
            scores.append({"platform": p, "content_type": ct, "score": score})
        return sorted(scores, key=lambda x: x["score"], reverse=True)[:count]

    def get_insights(self, platform: str = "",
                     priority: int = 0) -> List[ContentInsight]:
        results = self._insights
        if platform:
            results = [i for i in results if i.platform == platform]
        if priority > 0:
            results = [i for i in results if i.priority == priority]
        return results

    def get_stats(self) -> Dict[str, Any]:
        priorities: Dict[int, int] = {}
        for i in self._insights:
            priorities[i.priority] = priorities.get(i.priority, 0) + 1
        return {"total_insights": len(self._insights),
                "by_priority": priorities,
                "tracked_content_types": len(self._content_scores)}
