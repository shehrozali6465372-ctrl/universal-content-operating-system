"""Improvement Metrics — Track self-improvement performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class ImprovementMetrics:
    """Track metrics across self-improvement cycles."""

    def __init__(self) -> None:
        self._total_cycles: int = 0
        self._successful_cycles: int = 0
        self._total_mistakes_detected: int = 0
        self._total_weaknesses_found: int = 0
        self._total_actions_created: int = 0
        self._total_actions_completed: int = 0
        self._total_experiments: int = 0
        self._total_rollbacks: int = 0
        self._cycle_scores: List[float] = []

    def record_cycle(self, score: float = 0.0, successful: bool = False) -> None:
        self._total_cycles += 1
        if successful:
            self._successful_cycles += 1
        if score > 0:
            self._cycle_scores.append(score)

    def record_mistakes(self, count: int = 0) -> None:
        self._total_mistakes_detected += count

    def record_weaknesses(self, count: int = 0) -> None:
        self._total_weaknesses_found += count

    def record_action(self, completed: bool = False) -> None:
        self._total_actions_created += 1
        if completed:
            self._total_actions_completed += 1

    def record_experiment(self) -> None:
        self._total_experiments += 1

    def record_rollback(self) -> None:
        self._total_rollbacks += 1

    def get_cycle_success_rate(self) -> float:
        if self._total_cycles == 0:
            return 0.0
        return round(self._successful_cycles / self._total_cycles, 3)

    def get_action_completion_rate(self) -> float:
        if self._total_actions_created == 0:
            return 0.0
        return round(self._total_actions_completed / self._total_actions_created, 3)

    def get_avg_score(self) -> float:
        if not self._cycle_scores:
            return 0.0
        return round(sum(self._cycle_scores) / len(self._cycle_scores), 3)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_cycles": self._total_cycles,
            "successful_cycles": self._successful_cycles,
            "cycle_success_rate": self.get_cycle_success_rate(),
            "total_mistakes_detected": self._total_mistakes_detected,
            "total_weaknesses_found": self._total_weaknesses_found,
            "total_actions_created": self._total_actions_created,
            "total_actions_completed": self._total_actions_completed,
            "action_completion_rate": self.get_action_completion_rate(),
            "total_experiments": self._total_experiments,
            "total_rollbacks": self._total_rollbacks,
            "avg_score": self.get_avg_score(),
        }

    def reset(self) -> None:
        self._total_cycles = 0
        self._successful_cycles = 0
        self._total_mistakes_detected = 0
        self._total_weaknesses_found = 0
        self._total_actions_created = 0
        self._total_actions_completed = 0
        self._total_experiments = 0
        self._total_rollbacks = 0
        self._cycle_scores.clear()
