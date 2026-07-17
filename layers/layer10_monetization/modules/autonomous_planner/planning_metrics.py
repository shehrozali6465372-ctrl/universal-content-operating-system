"""PlanningMetrics — Track planning performance."""
from __future__ import annotations
from typing import Any, Dict, List


class PlanningMetrics:
    """Track plan success rate, completion rate, and efficiency."""

    def __init__(self) -> None:
        self._total_plans: int = 0
        self._successful_plans: int = 0
        self._failed_plans: int = 0
        self._execution_times: List[float] = []
        self._resource_efficiencies: List[float] = []
        self._decision_scores: List[float] = []

    def record_plan(self, success: bool = True, execution_time_ms: float = 0.0,
                    resource_efficiency: float = 0.0, decision_score: float = 0.0) -> None:
        self._total_plans += 1
        if success:
            self._successful_plans += 1
        else:
            self._failed_plans += 1
        if execution_time_ms > 0:
            self._execution_times.append(execution_time_ms)
        if resource_efficiency > 0:
            self._resource_efficiencies.append(resource_efficiency)
        if decision_score > 0:
            self._decision_scores.append(decision_score)

    def get_success_rate(self) -> float:
        if self._total_plans == 0:
            return 0.0
        return round(self._successful_plans / self._total_plans, 3)

    def get_completion_rate(self) -> float:
        return self.get_success_rate()

    def get_avg_execution_time(self) -> float:
        if not self._execution_times:
            return 0.0
        return round(sum(self._execution_times) / len(self._execution_times), 1)

    def get_avg_resource_efficiency(self) -> float:
        if not self._resource_efficiencies:
            return 0.0
        return round(sum(self._resource_efficiencies) / len(self._resource_efficiencies), 3)

    def get_avg_decision_score(self) -> float:
        if not self._decision_scores:
            return 0.0
        return round(sum(self._decision_scores) / len(self._decision_scores), 3)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_plans": self._total_plans, "successful": self._successful_plans,
            "failed": self._failed_plans, "success_rate": self.get_success_rate(),
            "avg_execution_time_ms": self.get_avg_execution_time(),
            "avg_resource_efficiency": self.get_avg_resource_efficiency(),
            "avg_decision_score": self.get_avg_decision_score(),
        }

    def reset(self) -> None:
        self._total_plans = 0
        self._successful_plans = 0
        self._failed_plans = 0
        self._execution_times.clear()
        self._resource_efficiencies.clear()
        self._decision_scores.clear()
