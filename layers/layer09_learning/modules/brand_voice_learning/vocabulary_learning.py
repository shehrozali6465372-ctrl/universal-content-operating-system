"""Vocabulary Learning — Learn vocabulary preferences from content performance."""
from __future__ import annotations
from typing import Any, Dict, List


class VocabularyInsight:
    """A single vocabulary learning insight."""

    __slots__ = ("word", "current_frequency", "suggested_frequency",
                 "performance_impact", "confidence", "action")

    def __init__(self, word: str = "") -> None:
        self.word = word
        self.current_frequency: float = 0.0
        self.suggested_frequency: float = 0.5
        self.performance_impact: float = 0.0
        self.confidence: float = 0.0
        self.action: str = "maintain"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "current_frequency": round(self.current_frequency, 3),
            "suggested_frequency": round(self.suggested_frequency, 3),
            "performance_impact": round(self.performance_impact, 3),
            "action": self.action,
        }


class VocabularyLearner:
    """Learn vocabulary patterns from content performance data."""

    def __init__(self) -> None:
        self._insights: List[VocabularyInsight] = []
        self._learning_count: int = 0

    def learn(
        self,
        current_vocabulary: Dict[str, float],
        word_performance: Dict[str, List[float]],
        min_samples: int = 2,
    ) -> List[VocabularyInsight]:
        self._insights.clear()
        for word, performances in word_performance.items():
            if len(performances) < min_samples:
                continue
            insight = VocabularyInsight(word)
            insight.current_frequency = current_vocabulary.get(word, 0.0)
            avg_perf = sum(performances) / len(performances)
            insight.performance_impact = round(avg_perf, 3)
            insight.suggested_frequency = round(min(1.0, max(0.0, avg_perf)), 3)
            insight.confidence = round(min(1.0, len(performances) / 10.0), 3)
            if avg_perf > 0.7 and insight.current_frequency < 0.5:
                insight.action = "increase"
            elif avg_perf < 0.3 and insight.current_frequency > 0.3:
                insight.action = "decrease"
            elif avg_perf < 0.2:
                insight.action = "avoid"
            else:
                insight.action = "maintain"
            self._insights.append(insight)
        self._learning_count += 1
        return list(self._insights)

    def get_increases(self) -> List[VocabularyInsight]:
        return [i for i in self._insights if i.action == "increase"]

    def get_decreases(self) -> List[VocabularyInsight]:
        return [i for i in self._insights if i.action in ("decrease", "avoid")]

    def get_insight(self, word: str) -> VocabularyInsight | None:
        for i in self._insights:
            if i.word == word:
                return i
        return None

    def get_insights(self) -> List[VocabularyInsight]:
        return list(self._insights)

    @property
    def learning_count(self) -> int:
        return self._learning_count
