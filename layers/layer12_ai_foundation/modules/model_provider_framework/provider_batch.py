"""provider_batch.py — Batch processing support."""
from __future__ import annotations
from typing import Any, Callable, Dict, List
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderRequest


class BatchJob:
    """A batch of requests to process."""
    __slots__ = ("job_id", "requests", "results", "status", "metadata")

    def __init__(self, job_id: str, requests: List[ProviderRequest]) -> None:
        self.job_id = job_id
        self.requests = requests
        self.results: list = []
        self.status: str = "pending"
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"job_id": self.job_id, "count": len(self.requests),
                "results_count": len(self.results), "status": self.status}


class ProviderBatch:
    """Manages batch processing of provider requests."""

    def __init__(self) -> None:
        self._jobs: Dict[str, BatchJob] = {}
        self._batch_size: int = 10

    def create_job(self, job_id: str, requests: List[ProviderRequest]) -> BatchJob:
        job = BatchJob(job_id, requests)
        self._jobs[job_id] = job
        return job

    def process(self, job_id: str, executor: Callable) -> BatchJob:
        job = self._jobs.get(job_id)
        if not job:
            return BatchJob(job_id, [])
        job.status = "running"
        for req in job.requests:
            try:
                result = executor(req)
                job.results.append(result)
            except Exception:
                job.results.append(None)
        job.status = "completed"
        return job

    def get_job(self, job_id: str) -> BatchJob:
        return self._jobs.get(job_id, BatchJob(job_id, []))

    def get_all_jobs(self) -> List[BatchJob]:
        return list(self._jobs.values())

    def clear(self) -> None:
        self._jobs.clear()
