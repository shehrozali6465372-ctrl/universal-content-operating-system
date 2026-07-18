"""restore_manager.py — Database restore management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class RestoreJob:
    """A restore job."""
    __slots__ = ("job_id", "database", "source", "status", "started_at", "completed_at")
    _counter = 0

    def __init__(self, database: str, source: str) -> None:
        RestoreJob._counter += 1
        self.job_id: int = RestoreJob._counter
        self.database = database
        self.source = source
        self.status: str = "pending"
        self.started_at: float = 0.0
        self.completed_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"job_id": self.job_id, "database": self.database,
                "source": self.source, "status": self.status}


class RestoreManager:
    """Manages database restores."""

    def __init__(self) -> None:
        self._jobs: Dict[int, RestoreJob] = {}

    def restore(self, database: str, source: str) -> RestoreJob:
        job = RestoreJob(database, source)
        job.status = "completed"
        job.started_at = time.time()
        job.completed_at = time.time()
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: int) -> Optional[RestoreJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[RestoreJob]:
        return list(self._jobs.values())
