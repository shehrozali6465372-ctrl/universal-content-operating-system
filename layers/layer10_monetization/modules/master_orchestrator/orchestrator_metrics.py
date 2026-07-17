"""Orchestrator Metrics — Track orchestration performance."""
from __future__ import annotations
from typing import Any, Dict, List


class OrchestratorMetrics:
    """Track metrics across orchestration runs."""

    def __init__(self) -> None:
        self._total_runs: int = 0
        self._successful_runs: int = 0
        self._failed_runs: int = 0
        self._total_layers_executed: int = 0
        self._durations: List[float] = []
        self._retry_counts: List[int] = []
        self._layer_stats: Dict[str, Dict[str, int]] = {}

    def record_run(self, success: bool = True, duration_ms: float = 0.0,
                   layers_executed: int = 0, retries: int = 0,
                   layer_names: List[str] = None) -> None:
        self._total_runs += 1
        if success:
            self._successful_runs += 1
        else:
            self._failed_runs += 1
        self._durations.append(duration_ms)
        self._total_layers_executed += layers_executed
        self._retry_counts.append(retries)
        for name in (layer_names or []):
            if name not in self._layer_stats:
                self._layer_stats[name] = {"executions": 0, "failures": 0}
            self._layer_stats[name]["executions"] += 1

    def record_layer_failure(self, layer: str) -> None:
        if layer not in self._layer_stats:
            self._layer_stats[layer] = {"executions": 0, "failures": 0}
        self._layer_stats[layer]["failures"] += 1

    def get_success_rate(self) -> float:
        if self._total_runs == 0:
            return 0.0
        return round(self._successful_runs / self._total_runs, 3)

    def get_avg_duration(self) -> float:
        if not self._durations:
            return 0.0
        return round(sum(self._durations) / len(self._durations), 1)

    def get_avg_retries(self) -> float:
        if not self._retry_counts:
            return 0.0
        return round(sum(self._retry_counts) / len(self._retry_counts), 2)

    def get_throughput(self) -> float:
        if not self._durations:
            return 0.0
        total_time = sum(self._durations) / 1000
        if total_time <= 0:
            return 0.0
        return round(self._total_runs / total_time, 2)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_runs": self._total_runs,
            "successful_runs": self._successful_runs,
            "failed_runs": self._failed_runs,
            "success_rate": self.get_success_rate(),
            "total_layers_executed": self._total_layers_executed,
            "avg_duration_ms": self.get_avg_duration(),
            "avg_retries": self.get_avg_retries(),
            "throughput_per_sec": self.get_throughput(),
        }

    def reset(self) -> None:
        self._total_runs = 0
        self._successful_runs = 0
        self._failed_runs = 0
        self._total_layers_executed = 0
        self._durations.clear()
        self._retry_counts.clear()
        self._layer_stats.clear()
