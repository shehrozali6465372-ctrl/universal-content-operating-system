"""ResourceManager — Manage CPU, memory, workers, threads."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import ResourceMetrics


class ResourceManager:
    """Track and manage system resources."""

    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000) -> None:
        self._max_workers: int = max_workers
        self._max_queue_size: int = max_queue_size
        self._active_workers: int = 0
        self._idle_workers: int = max_workers
        self._lock = threading.RLock()

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: int) -> None:
        with self._lock:
            self._max_workers = value

    def acquire_worker(self) -> bool:
        with self._lock:
            if self._active_workers < self._max_workers:
                self._active_workers += 1
                self._idle_workers = self._max_workers - self._active_workers
                return True
            return False

    def release_worker(self) -> None:
        with self._lock:
            self._active_workers = max(0, self._active_workers - 1)
            self._idle_workers = self._max_workers - self._active_workers

    def get_metrics(self) -> ResourceMetrics:
        with self._lock:
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_mb=0.0,
                workers_active=self._active_workers,
                workers_idle=self._idle_workers,
                queue_size=0,
                threads=threading.active_count(),
            )

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "max_workers": self._max_workers,
                "active_workers": self._active_workers,
                "idle_workers": self._idle_workers,
                "max_queue_size": self._max_queue_size,
            }
