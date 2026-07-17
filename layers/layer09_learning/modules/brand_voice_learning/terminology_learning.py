"""Terminology Learning — Learn terminology usage from content performance."""
from __future__ import annotations
from typing import Any, Dict, List


class TerminologyInsight:
    """A single terminology learning insight."""

    __slots__ = ("term", "current_definition", "usage_frequency",
                 "performance_impact", "confidence", "action")

    def __init__(self, term: str = "") -> None:
        self.term = term
        self.current_definition: str = ""
        self.usage_frequency: float = 0.0
        self.performance_impact: float = 0.0
        self.confidence: float = 0.0
        self.action: str = "maintain"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "usage_frequency": round(self.usage_frequency, 3),
            "performance_impact": round(self.performance_impact, 3),
            "action": self.action,
        }


class TerminologyLearner:
    """Learn terminology patterns from content performance data."""

    def __init__(self) -> None:
        self._insights: List[TerminologyInsight] = []
        self._learning_count: int = 0

    def learn(
        self,
        current_terminology: Dict[str, str],
        term_performance: Dict[str, List[float]],
        min_samples: int = 2,
    ) -> List[TerminologyInsight]:
        self._insights.clear()
        for term, performances in term_performance.items():
            if len(performances) < min_samples:
                continue
            insight = TerminologyInsight(term)
            insight.current_definition = current_terminology.get(term, "")
            insight.usage_frequency = round(len(performances) / 100.0, 3)
            avg_perf = sum(performances) / len(performances)
            insight.performance_impact = round(avg_perf, 3)
            insight.confidence = round(min(1.0, len(performances) / 10.0), 3)
            if avg_perf > 0.7:
                insight.action = "emphasize"
            elif avg_perf < 0.3:
                insight.action = "simplify"
            else:
                insight.action = "maintain"
            self._insights.append(insight)
        self._learning_count += 1
        return list(self._insights)

    def get_emphasized(self) -> List[TerminologyInsight]:
        return [i for i in self._insights if i.action == "emphasize"]

    def get_simplified(self) -> List[TerminologyInsight]:
        return [i for i in self._insights if i.action == "simplify"]

    def get_insight(self, term: str) -> TerminologyInsight | None:
        for i in self._insights:
            if i.term == term:
                return i
        return None

    def get_insights(self) -> List[TerminologyInsight]:
        return list(self._insights)

    @property
    def learning_count(self) -> int:
        return self._learning_count
