"""Learning Metrics — Track learning score, improvement rate, success rate."""
from __future__ import annotations
from typing import Any, Dict, List


class LearningMetrics:
    """Track and report learning performance metrics."""

    def __init__(self) -> None:
        self._total_lessons: int = 0
        self._total_improvements: int = 0
        self._total_patterns: int = 0
        self._total_signals: int = 0
        self._successful_improvements: int = 0
        self._learning_scores: List[float] = []

    def record_learning_cycle(
        self,
        signals: int = 0,
        patterns: int = 0,
        lessons: int = 0,
        improvements: int = 0,
    ) -> None:
        self._total_signals += signals
        self._total_patterns += patterns
        self._total_lessons += lessons
        self._total_improvements += improvements
        score = self._calculate_score(signals, patterns, lessons, improvements)
        self._learning_scores.append(score)

    def record_improvement_outcome(self, successful: bool) -> None:
        if successful:
            self._successful_improvements += 1

    def get_score(self) -> float:
        if not self._learning_scores:
            return 0.0
        return round(self._learning_scores[-1], 2)

    def get_avg_score(self) -> float:
        if not self._learning_scores:
            return 0.0
        return round(sum(self._learning_scores) / len(self._learning_scores), 2)

    def get_improvement_rate(self) -> float:
        if self._total_improvements == 0:
            return 0.0
        return round(self._successful_improvements / self._total_improvements, 3)

    def get_learning_efficiency(self) -> float:
        if self._total_signals == 0:
            return 0.0
        return round(self._total_lessons / max(1, self._total_signals) * 100, 2)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_signals": self._total_signals,
            "total_patterns": self._total_patterns,
            "total_lessons": self._total_lessons,
            "total_improvements": self._total_improvements,
            "successful_improvements": self._successful_improvements,
            "current_score": self.get_score(),
            "avg_score": self.get_avg_score(),
            "improvement_rate": self.get_improvement_rate(),
            "learning_efficiency": self.get_learning_efficiency(),
        }

    def _calculate_score(self, signals: int, patterns: int, lessons: int, improvements: int) -> float:
        if signals == 0:
            return 0.0
        pattern_ratio = min(1.0, patterns / max(1, signals))
        lesson_ratio = min(1.0, lessons / max(1, patterns))
        improvement_ratio = min(1.0, improvements / max(1, lessons))
        return round((pattern_ratio * 0.3 + lesson_ratio * 0.35 + improvement_ratio * 0.35) * 100, 2)

    def reset(self) -> None:
        self._total_lessons = 0
        self._total_improvements = 0
        self._total_patterns = 0
        self._total_signals = 0
        self._successful_improvements = 0
        self._learning_scores.clear()
