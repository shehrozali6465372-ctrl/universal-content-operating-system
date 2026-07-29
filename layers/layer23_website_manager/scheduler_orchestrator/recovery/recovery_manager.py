"""RecoveryManager — Recover interrupted or crashed jobs."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    ScheduledJob, JobStatus,
)
from layers.layer23_website_manager.scheduler_orchestrator.exceptions import RecoveryError


class RecoveryManager:
    """Handle recovery of failed/interrupted jobs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._recovery_log: List[Dict[str, Any]] = []

    def recover_job(self, job: ScheduledJob) -> bool:
        if job.status in (JobStatus.RUNNING, JobStatus.FAILED, JobStatus.RETRYING):
            with self._lock:
                job.retry_count += 1
                job.status = JobStatus.PENDING
                job.scheduled_time = time.time() + 30
                self._recovery_log.append({
                    "job_id": job.job_id,
                    "action": "recovered",
                    "previous_status": job.status.value,
                    "retry_count": job.retry_count,
                    "timestamp": time.time(),
                })
            return True
        return False

    def recover_all_failed(self, jobs: List[ScheduledJob]) -> int:
        count = 0
        for job in jobs:
            if self.recover_job(job):
                count += 1
        return count

    def get_recovery_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return self._recovery_log[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_recoveries": len(self._recovery_log),
                "last_recovery": self._recovery_log[-1]["timestamp"] if self._recovery_log else None,
            }
