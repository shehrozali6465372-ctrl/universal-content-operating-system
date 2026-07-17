"""Scheduler Metrics — Track scheduling performance."""
from __future__ import annotations
from typing import Any, Dict, List


class SchedulerMetrics:
    """Track metrics across scheduling operations."""

    def __init__(self) -> None:
        self._total_scheduled: int = 0
        self._total_completed: int = 0
        self._total_failed: int = 0
        self._total_retries: int = 0
        self._wait_times: List[float] = []
        self._execution_times: List[float] = []
        self._queue_sizes: List[int] = []
        self._worker_utilizations: List[float] = []

    def record_task_scheduled(self) -> None:
        self._total_scheduled += 1

    def record_task_completed(self, wait_time_ms: float = 0.0,
                               execution_time_ms: float = 0.0) -> None:
        self._total_completed += 1
        if wait_time_ms > 0:
            self._wait_times.append(wait_time_ms)
        if execution_time_ms > 0:
            self._execution_times.append(execution_time_ms)

    def record_task_failed(self) -> None:
        self._total_failed += 1

    def record_retry(self) -> None:
        self._total_retries += 1

    def record_queue_size(self, size: int) -> None:
        self._queue_sizes.append(size)

    def record_worker_utilization(self, utilization: float) -> None:
        self._worker_utilizations.append(utilization)

    def get_throughput(self) -> float:
        if not self._execution_times:
            return 0.0
        total_time = sum(self._execution_times) / 1000
        return round(self._total_completed / max(0.001, total_time), 2)

    def get_avg_wait_time(self) -> float:
        if not self._wait_times:
            return 0.0
        return round(sum(self._wait_times) / len(self._wait_times), 1)

    def get_avg_execution_time(self) -> float:
        if not self._execution_times:
            return 0.0
        return round(sum(self._execution_times) / len(self._execution_times), 1)

    def get_avg_queue_size(self) -> float:
        if not self._queue_sizes:
            return 0.0
        return round(sum(self._queue_sizes) / len(self._queue_sizes), 1)

    def get_avg_worker_utilization(self) -> float:
        if not self._worker_utilizations:
            return 0.0
        return round(sum(self._worker_utilizations) / len(self._worker_utilizations), 3)

    def get_scheduling_efficiency(self) -> float:
        if self._total_scheduled == 0:
            return 0.0
        return round(self._total_completed / self._total_scheduled, 3)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_scheduled": self._total_scheduled,
            "total_completed": self._total_completed,
            "total_failed": self._total_failed,
            "total_retries": self._total_retries,
            "throughput_per_sec": self.get_throughput(),
            "avg_wait_time_ms": self.get_avg_wait_time(),
            "avg_execution_time_ms": self.get_avg_execution_time(),
            "avg_queue_size": self.get_avg_queue_size(),
            "avg_worker_utilization": self.get_avg_worker_utilization(),
            "scheduling_efficiency": self.get_scheduling_efficiency(),
        }

    def reset(self) -> None:
        self._total_scheduled = 0
        self._total_completed = 0
        self._total_failed = 0
        self._total_retries = 0
        self._wait_times.clear()
        self._execution_times.clear()
        self._queue_sizes.clear()
        self._worker_utilizations.clear()
