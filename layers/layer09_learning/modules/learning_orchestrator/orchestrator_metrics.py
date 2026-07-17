"""Orchestrator Metrics — Track orchestration performance."""
from __future__ import annotations
from typing import Any, Dict, List


class OrchestratorMetrics:
    """Track metrics across orchestration runs."""

    def __init__(self) -> None:
        self._total_runs: int = 0
        self._successful_runs: int = 0
        self._failed_runs: int = 0
        self._total_lessons: int = 0
        self._total_improvements: int = 0
        self._total_mistakes: int = 0
        self._durations: List[float] = []
        self._learning_scores: List[float] = []

    def record_run(self, success: bool = True, duration_ms: float = 0.0,
                   lessons: int = 0, improvements: int = 0, mistakes: int = 0,
                   learning_score: float = 0.0) -> None:
        self._total_runs += 1
        if success:
            self._successful_runs += 1
        else:
            self._failed_runs += 1
        self._durations.append(duration_ms)
        self._total_lessons += lessons
        self._total_improvements += improvements
        self._total_mistakes += mistakes
        if learning_score > 0:
            self._learning_scores.append(learning_score)

    def get_success_rate(self) -> float:
        if self._total_runs == 0:
            return 0.0
        return round(self._successful_runs / self._total_runs, 3)

    def get_avg_duration(self) -> float:
        if not self._durations:
            return 0.0
        return round(sum(self._durations) / len(self._durations), 1)

    def get_avg_learning_score(self) -> float:
        if not self._learning_scores:
            return 0.0
        return round(sum(self._learning_scores) / len(self._learning_scores), 1)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_runs": self._total_runs,
            "successful_runs": self._successful_runs,
            "failed_runs": self._failed_runs,
            "success_rate": self.get_success_rate(),
            "total_lessons": self._total_lessons,
            "total_improvements": self._total_improvements,
            "total_mistakes": self._total_mistakes,
            "avg_duration_ms": self.get_avg_duration(),
            "avg_learning_score": self.get_avg_learning_score(),
        }

    def reset(self) -> None:
        self._total_runs = 0
        self._successful_runs = 0
        self._failed_runs = 0
        self._total_lessons = 0
        self._total_improvements = 0
        self._total_mistakes = 0
        self._durations.clear()
        self._learning_scores.clear()
