"""provider_fine_tune.py — Fine-tuning support."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_FT_ID = itertools.count(1)


class FineTuneJob:
    """Represents a fine-tuning job."""
    __slots__ = ("job_id", "model", "provider", "status", "training_file",
                 "created_at", "metadata")

    def __init__(self, model: str, provider: str, training_file: str = "") -> None:
        self.job_id = f"ft_{next(_FT_ID)}"
        self.model = model
        self.provider = provider
        self.status: str = "created"
        self.training_file = training_file
        self.created_at: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"job_id": self.job_id, "model": self.model, "provider": self.provider,
                "status": self.status}


class ProviderFineTune:
    """Manages fine-tuning jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, FineTuneJob] = {}

    def create_job(self, model: str, provider: str,
                   training_file: str = "") -> FineTuneJob:
        job = FineTuneJob(model, provider, training_file)
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[FineTuneJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, provider: str = "") -> List[FineTuneJob]:
        jobs = list(self._jobs.values())
        if provider:
            jobs = [j for j in jobs if j.provider == provider]
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.status = "cancelled"
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        statuses = {}
        for j in self._jobs.values():
            statuses[j.status] = statuses.get(j.status, 0) + 1
        return {"total_jobs": len(self._jobs), "by_status": statuses}
