"""Meta Metrics — System-wide performance metrics."""
from __future__ import annotations
from typing import Any, Dict


class MetaMetrics:
    """Track AI accuracy, goal completion, and system performance."""

    def __init__(self) -> None:
        self._metrics: Dict[str, float] = {
            "ai_accuracy": 0.0, "goal_completion_rate": 0.0,
            "decision_accuracy": 0.0, "automation_rate": 0.0,
            "recovery_rate": 0.0, "learning_rate": 0.0,
            "revenue_growth": 0.0, "performance_score": 0.0,
        }
        self._counters: Dict[str, int] = {
            "total_decisions": 0, "correct_decisions": 0,
            "total_goals": 0, "completed_goals": 0,
            "total_recoveries": 0, "successful_recoveries": 0,
        }

    def record_decision(self, correct: bool = True) -> None:
        self._counters["total_decisions"] += 1
        if correct:
            self._counters["correct_decisions"] += 1
        self._update_rate("decision_accuracy",
                          self._counters["correct_decisions"],
                          self._counters["total_decisions"])

    def record_goal(self, completed: bool = True) -> None:
        self._counters["total_goals"] += 1
        if completed:
            self._counters["completed_goals"] += 1
        self._update_rate("goal_completion_rate",
                          self._counters["completed_goals"],
                          self._counters["total_goals"])

    def record_recovery(self, successful: bool = True) -> None:
        self._counters["total_recoveries"] += 1
        if successful:
            self._counters["successful_recoveries"] += 1
        self._update_rate("recovery_rate",
                          self._counters["successful_recoveries"],
                          self._counters["total_recoveries"])

    def set_metric(self, name: str, value: float) -> None:
        self._metrics[name] = value

    def get_metric(self, name: str) -> float:
        return self._metrics.get(name, 0.0)

    def _update_rate(self, metric: str, numerator: int, denominator: int) -> None:
        if denominator > 0:
            self._metrics[metric] = round(numerator / denominator, 3)

    def get_summary(self) -> Dict[str, Any]:
        return {**self._metrics, **self._counters}

    def reset(self) -> None:
        for k in self._metrics:
            self._metrics[k] = 0.0
        for k in self._counters:
            self._counters[k] = 0
