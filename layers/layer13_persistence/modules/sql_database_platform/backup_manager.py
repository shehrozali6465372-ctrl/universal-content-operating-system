"""backup_manager.py — Database backup management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class BackupJob:
    """A backup job."""
    __slots__ = ("job_id", "backup_type", "database", "status", "started_at",
                 "completed_at", "size_bytes", "path")
    _counter = 0

    def __init__(self, backup_type: str, database: str) -> None:
        BackupJob._counter += 1
        self.job_id: int = BackupJob._counter
        self.backup_type = backup_type
        self.database = database
        self.status: str = "pending"
        self.started_at: float = 0.0
        self.completed_at: float = 0.0
        self.size_bytes: int = 0
        self.path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"job_id": self.job_id, "type": self.backup_type,
                "database": self.database, "status": self.status}


class BackupManager:
    """Manages database backups."""

    def __init__(self) -> None:
        self._jobs: Dict[int, BackupJob] = {}
        self._completed: List[BackupJob] = []

    def create_full_backup(self, database: str) -> BackupJob:
        job = BackupJob("full", database)
        job.status = "completed"
        job.started_at = time.time()
        job.completed_at = time.time()
        self._jobs[job.job_id] = job
        self._completed.append(job)
        return job

    def create_incremental_backup(self, database: str) -> BackupJob:
        job = BackupJob("incremental", database)
        job.status = "completed"
        job.started_at = time.time()
        job.completed_at = time.time()
        self._jobs[job.job_id] = job
        self._completed.append(job)
        return job

    def get_job(self, job_id: int) -> Optional[BackupJob]:
        return self._jobs.get(job_id)

    def get_completed(self) -> List[BackupJob]:
        return list(self._completed)

    def stats(self) -> Dict[str, Any]:
        return {"total_jobs": len(self._jobs), "completed": len(self._completed)}
