"""Style Learning — Learn writing style preferences from performance feedback."""
from __future__ import annotations
from typing import Any, Dict, List


class StyleInsight:
    """A single style learning insight."""

    __slots__ = ("style_element", "current_value", "suggested_value",
                 "performance_score", "confidence", "reason")

    def __init__(self, style_element: str = "") -> None:
        self.style_element = style_element
        self.current_value: str = ""
        self.suggested_value: str = ""
        self.performance_score: float = 0.0
        self.confidence: float = 0.0
        self.reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "style_element": self.style_element,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "performance_score": round(self.performance_score, 3),
            "confidence": round(self.confidence, 3),
        }


class StyleLearner:
    """Learn writing style patterns from content performance data."""

    def __init__(self) -> None:
        self._insights: List[StyleInsight] = []
        self._learning_count: int = 0

    def learn(
        self,
        current_style: Dict[str, str],
        style_performance: Dict[str, Dict[str, List[float]]],
        min_samples: int = 2,
    ) -> List[StyleInsight]:
        self._insights.clear()
        for style_element, value_scores in style_performance.items():
            best_value = None
            best_score = -1.0
            total_samples = 0
            for value, scores in value_scores.items():
                if len(scores) < min_samples:
                    continue
                total_samples += len(scores)
                avg = sum(scores) / len(scores)
                if avg > best_score:
                    best_score = avg
                    best_value = value
            if best_value is not None:
                insight = StyleInsight(style_element)
                insight.current_value = current_style.get(style_element, "")
                insight.suggested_value = best_value
                insight.performance_score = round(best_score, 3)
                insight.confidence = round(min(1.0, total_samples / 20.0), 3)
                insight.reason = f"Best performing value: {best_value} (score: {best_score:.2f})"
                self._insights.append(insight)
        self._learning_count += 1
        return list(self._insights)

    def get_suggestions(self) -> List[StyleInsight]:
        return [i for i in self._insights if i.suggested_value != i.current_value]

    def get_insight(self, style_element: str) -> StyleInsight | None:
        for i in self._insights:
            if i.style_element == style_element:
                return i
        return None

    def get_insights(self) -> List[StyleInsight]:
        return list(self._insights)

    @property
    def learning_count(self) -> int:
        return self._learning_count
