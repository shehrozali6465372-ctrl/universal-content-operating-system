"""Metrics Collector — Collect pipeline execution metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class PipelineMetrics:
    """Collected pipeline metrics."""

    __slots__ = ("total_executions", "success_count", "failure_count",
                 "avg_duration_ms", "total_duration_ms",
                 "avg_stages_completed", "error_rate")

    def __init__(self) -> None:
        self.total_executions: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.avg_duration_ms: float = 0.0
        self.total_duration_ms: float = 0.0
        self.avg_stages_completed: float = 0.0
        self.error_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "error_rate": round(self.error_rate, 3),
        }


class MetricsCollector:
    """Collect and aggregate pipeline metrics."""

    def __init__(self) -> None:
        self._executions: List[Dict[str, Any]] = []

    def record(self, success: bool, duration_ms: float, stages_completed: int) -> None:
        self._executions.append({
            "success": success,
            "duration_ms": duration_ms,
            "stages_completed": stages_completed,
        })

    def get_metrics(self) -> PipelineMetrics:
        m = PipelineMetrics()
        if not self._executions:
            return m
        m.total_executions = len(self._executions)
        m.success_count = sum(1 for e in self._executions if e["success"])
        m.failure_count = m.total_executions - m.success_count
        m.total_duration_ms = sum(e["duration_ms"] for e in self._executions)
        m.avg_duration_ms = m.total_duration_ms / max(1, m.total_executions)
        m.avg_stages_completed = sum(e["stages_completed"] for e in self._executions) / max(1, m.total_executions)
        m.error_rate = m.failure_count / max(1, m.total_executions)
        return m

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._executions)
