"""RetryManager — Retry failed jobs with exponential backoff."""
from __future__ import annotations
import time
import random
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    ScheduledJob, JobStatus, Priority,
)
from layers.layer23_website_manager.scheduler_orchestrator.exceptions import RetryError


class RetryManager:
    """Manage retry logic for failed jobs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._retry_history: Dict[str, List[Dict[str, Any]]] = {}

    def should_retry(self, job: ScheduledJob) -> bool:
        return job.retry_count < job.max_retries

    def calculate_backoff(self, retry_count: int, base_delay: float = 5.0) -> float:
        delay = base_delay * (2 ** retry_count)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    def record_retry(self, job: ScheduledJob, error: str = "") -> Dict[str, Any]:
        with self._lock:
            job.retry_count += 1
            backoff = self.calculate_backoff(job.retry_count)
            entry = {
                "retry": job.retry_count,
                "max": job.max_retries,
                "backoff_seconds": round(backoff, 1),
                "error": error,
                "timestamp": time.time(),
            }
            if job.job_id not in self._retry_history:
                self._retry_history[job.job_id] = []
            self._retry_history[job.job_id].append(entry)
            return entry

    def get_retry_history(self, job_id: str) -> List[Dict[str, Any]]:
        return self._retry_history.get(job_id, [])

    def reset_retries(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._retry_history:
                self._retry_history[job_id].clear()
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_retries = sum(len(h) for h in self._retry_history.values())
            jobs_with_retries = sum(1 for h in self._retry_history.values() if h)
            return {
                "total_retries": total_retries,
                "jobs_with_retries": jobs_with_retries,
                "tracked_jobs": len(self._retry_history),
            }
