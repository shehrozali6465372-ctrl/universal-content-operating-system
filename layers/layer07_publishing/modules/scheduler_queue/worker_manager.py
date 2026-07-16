"""Worker Manager — Manage worker pool for job execution."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class Worker:
    def __init__(self, worker_id: str = "") -> None:
        self.worker_id = worker_id
        self.busy: bool = False
        self.jobs_processed: int = 0
        self.current_job: Optional[str] = None

    def to_dict(self) -> dict:
        return {"worker_id": self.worker_id, "busy": self.busy, "jobs_processed": self.jobs_processed}


class WorkerManager:
    def __init__(self, pool_size: int = 3) -> None:
        self._workers = [Worker(f"worker_{i}") for i in range(pool_size)]
        self._total_processed = 0

    def get_idle_worker(self) -> Optional[Worker]:
        for w in self._workers:
            if not w.busy:
                return w
        return None

    def assign_job(self, worker_id: str, job: PublishJob) -> bool:
        for w in self._workers:
            if w.worker_id == worker_id and not w.busy:
                w.busy = True
                w.current_job = job.job_id
                return True
        return False

    def complete_job(self, worker_id: str) -> None:
        for w in self._workers:
            if w.worker_id == worker_id:
                w.busy = False
                w.current_job = None
                w.jobs_processed += 1
                self._total_processed += 1

    def get_workers(self) -> List[Dict[str, Any]]:
        return [w.to_dict() for w in self._workers]

    def idle_count(self) -> int:
        return sum(1 for w in self._workers if not w.busy)

    def busy_count(self) -> int:
        return sum(1 for w in self._workers if w.busy)

    @property
    def pool_size(self) -> int:
        return len(self._workers)

    @property
    def total_processed(self) -> int:
        return self._total_processed
