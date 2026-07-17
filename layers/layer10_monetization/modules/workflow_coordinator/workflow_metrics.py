"""Workflow Metrics — Track workflow performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class WorkflowMetrics:
    """Track metrics across workflow executions."""

    def __init__(self) -> None:
        self._total_runs: int = 0
        self._successful_runs: int = 0
        self._failed_runs: int = 0
        self._total_retries: int = 0
        self._durations: List[float] = []
        self._stage_durations: Dict[str, List[float]] = {}
        self._failed_stages: Dict[str, int] = {}

    def record_run(self, success: bool = True, duration_ms: float = 0.0,
                   retries: int = 0, stage_count: int = 0) -> None:
        self._total_runs += 1
        if success:
            self._successful_runs += 1
        else:
            self._failed_runs += 1
        self._durations.append(duration_ms)
        self._total_retries += retries

    def record_stage(self, layer: str, duration_ms: float, success: bool = True) -> None:
        if layer not in self._stage_durations:
            self._stage_durations[layer] = []
        self._stage_durations[layer].append(duration_ms)
        if not success:
            self._failed_stages[layer] = self._failed_stages.get(layer, 0) + 1

    def get_success_rate(self) -> float:
        if self._total_runs == 0:
            return 0.0
        return round(self._successful_runs / self._total_runs, 3)

    def get_avg_duration(self) -> float:
        if not self._durations:
            return 0.0
        return round(sum(self._durations) / len(self._durations), 1)

    def get_avg_retries(self) -> float:
        if self._total_runs == 0:
            return 0.0
        return round(self._total_retries / self._total_runs, 2)

    def get_stage_avg_duration(self, layer: str) -> float:
        durations = self._stage_durations.get(layer, [])
        if not durations:
            return 0.0
        return round(sum(durations) / len(durations), 1)

    def get_failed_stages(self) -> Dict[str, int]:
        return dict(self._failed_stages)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_runs": self._total_runs,
            "successful_runs": self._successful_runs,
            "failed_runs": self._failed_runs,
            "success_rate": self.get_success_rate(),
            "total_retries": self._total_retries,
            "avg_duration_ms": self.get_avg_duration(),
            "avg_retries_per_run": self.get_avg_retries(),
            "failed_stages": self.get_failed_stages(),
        }

    def reset(self) -> None:
        self._total_runs = 0
        self._successful_runs = 0
        self._failed_runs = 0
        self._total_retries = 0
        self._durations.clear()
        self._stage_durations.clear()
        self._failed_stages.clear()
