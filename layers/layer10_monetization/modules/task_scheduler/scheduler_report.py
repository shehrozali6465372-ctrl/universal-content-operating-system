"""Scheduler Report — Generate scheduling reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_SR_COUNTER = itertools.count(1)


class SchedulerReport:
    """Report from scheduling operations."""

    __slots__ = ("report_id", "queue_report", "worker_report", "resource_report",
                 "performance_report", "recommendations", "timestamp")

    def __init__(self) -> None:
        self.report_id: str = f"srep_{next(_SR_COUNTER)}"
        self.queue_report: Dict[str, Any] = {}
        self.worker_report: Dict[str, Any] = {}
        self.resource_report: Dict[str, Any] = {}
        self.performance_report: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()

    def set_queue_report(self, total: int, by_priority: Dict[str, int],
                          avg_wait_ms: float = 0.0) -> None:
        self.queue_report = {
            "total_tasks": total,
            "by_priority": by_priority,
            "avg_wait_ms": round(avg_wait_ms, 1),
        }

    def set_worker_report(self, pool_size: int, idle: int, busy: int,
                           completed: int = 0) -> None:
        self.worker_report = {
            "pool_size": pool_size,
            "idle": idle,
            "busy": busy,
            "utilization": round(busy / max(1, pool_size), 3),
            "tasks_completed": completed,
        }

    def set_resource_report(self, utilization: Dict[str, float]) -> None:
        self.resource_report = dict(utilization)

    def set_performance_report(self, throughput: float, efficiency: float,
                                avg_exec_ms: float = 0.0) -> None:
        self.performance_report = {
            "throughput_per_sec": throughput,
            "scheduling_efficiency": efficiency,
            "avg_execution_time_ms": round(avg_exec_ms, 1),
        }

    def add_recommendation(self, recommendation: str) -> None:
        self.recommendations.append(recommendation)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "queue_size": self.queue_report.get("total_tasks", 0),
            "worker_utilization": self.worker_report.get("utilization", 0.0),
            "throughput": self.performance_report.get("throughput_per_sec", 0.0),
            "efficiency": self.performance_report.get("scheduling_efficiency", 0.0),
            "recommendation_count": len(self.recommendations),
        }

    def export_dict(self) -> Dict[str, Any]:
        return {
            **self.get_summary(),
            "queue_report": self.queue_report,
            "worker_report": self.worker_report,
            "resource_report": self.resource_report,
            "performance_report": self.performance_report,
            "recommendations": self.recommendations,
        }
