"""Batch Publisher — Execute multiple jobs in batch with grouping."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class BatchResult:
    def __init__(self, batch_id: str = "") -> None:
        self.batch_id = batch_id
        self.total_jobs: int = 0
        self.completed: int = 0
        self.failed: int = 0
        self.results: List[Dict[str, Any]] = []
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "total_jobs": self.total_jobs,
            "completed": self.completed,
            "failed": self.failed,
            "success_rate": round(self.completed / max(1, self.total_jobs), 3),
            "duration_ms": round(self.duration_ms, 2),
        }


class BatchPublisher:
    def __init__(self) -> None:
        self._batch_count = 0

    def execute_batch(
        self,
        jobs: List[PublishJob],
        executor: Callable[[PublishJob], bool],
    ) -> BatchResult:
        result = BatchResult(f"batch_{self._batch_count}")
        result.total_jobs = len(jobs)
        start = time.time()

        for job in jobs:
            job.status = "running"
            job.started_at = time.time()
            try:
                success = executor(job)
                if success:
                    job.status = "completed"
                    job.completed_at = time.time()
                    result.completed += 1
                else:
                    job.status = "failed"
                    result.failed += 1
            except Exception as e:
                job.status = "failed"
                job.last_error = str(e)[:200]
                result.failed += 1

            result.results.append({"job_id": job.job_id, "status": job.status})

        result.duration_ms = (time.time() - start) * 1000
        self._batch_count += 1
        return result

    def group_by_platform(self, jobs: List[PublishJob]) -> Dict[str, List[PublishJob]]:
        groups: Dict[str, List[PublishJob]] = {}
        for job in jobs:
            groups.setdefault(job.platform, []).append(job)
        return groups

    @property
    def batch_count(self) -> int:
        return self._batch_count
