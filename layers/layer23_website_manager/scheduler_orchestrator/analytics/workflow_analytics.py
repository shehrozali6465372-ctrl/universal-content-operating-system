"""WorkflowAnalyticsCollector — Track workflow performance metrics."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    WorkflowAnalytics, ExecutionLog,
)


class WorkflowAnalyticsCollector:
    """Collect and analyze workflow execution metrics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._logs: List[ExecutionLog] = []
        self._analytics: Dict[str, WorkflowAnalytics] = {}

    def record_execution(self, log: ExecutionLog) -> None:
        with self._lock:
            self._logs.append(log)

    def get_analytics(self, period: str = "all_time") -> WorkflowAnalytics:
        with self._lock:
            ana = WorkflowAnalytics()
            ana.period = period
            ana.total_jobs = len(self._logs)
            durations = []
            for log in self._logs:
                if log.status == "completed":
                    ana.completed += 1
                    durations.append(log.duration_ms)
                elif log.status == "failed":
                    ana.failed += 1
                elif log.status == "running":
                    ana.running += 1
                else:
                    ana.pending += 1
            if ana.total_jobs > 0:
                ana.success_rate = (ana.completed / ana.total_jobs) * 100
            if durations:
                ana.avg_duration_ms = sum(durations) / len(durations)
            return ana

    def get_stats(self) -> Dict[str, Any]:
        ana = self.get_analytics()
        return {
            "total_jobs": ana.total_jobs,
            "completed": ana.completed,
            "failed": ana.failed,
            "running": ana.running,
            "pending": ana.pending,
            "success_rate": round(ana.success_rate, 1),
            "avg_duration_ms": round(ana.avg_duration_ms, 1),
        }
