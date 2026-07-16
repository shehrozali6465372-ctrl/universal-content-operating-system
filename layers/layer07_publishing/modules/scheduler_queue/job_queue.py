"""Job Queue — Priority-based job queue for publishing."""
from __future__ import annotations
from typing import Dict, List, Optional

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class JobQueue:
    """Simple priority-based job queue."""

    def __init__(self, max_size: int = 10000) -> None:
        self._max_size = max_size
        self._jobs: Dict[str, PublishJob] = {}
        self._enqueue_count = 0
        self._dequeue_count = 0

    def enqueue(self, job: PublishJob) -> bool:
        """Add a job to the queue."""
        if len(self._jobs) >= self._max_size:
            return False
        self._jobs[job.job_id] = job
        self._enqueue_count += 1
        return True

    def enqueue_batch(self, jobs: List[PublishJob]) -> int:
        """Add multiple jobs."""
        count = 0
        for job in jobs:
            if self.enqueue(job):
                count += 1
        return count

    def dequeue(self, platform: Optional[str] = None) -> Optional[PublishJob]:
        """Get the next ready job. Optionally filter by platform."""
        ready = [
            j for j in self._jobs.values()
            if j.is_ready() and (platform is None or j.platform == platform)
        ]
        if not ready:
            return None
        ready.sort(key=lambda j: (j.priority, j.created_at))
        job = ready[0]
        job.status = "running"
        self._dequeue_count += 1
        return job

    def dequeue_many(self, count: int, platform: Optional[str] = None) -> List[PublishJob]:
        """Dequeue multiple jobs at once."""
        jobs: List[PublishJob] = []
        for _ in range(count):
            job = self.dequeue(platform)
            if job:
                jobs.append(job)
            else:
                break
        return jobs

    def peek(self, platform: Optional[str] = None) -> Optional[PublishJob]:
        """Look at next ready job without dequeuing."""
        ready = [
            j for j in self._jobs.values()
            if j.is_ready() and (platform is None or j.platform == platform)
        ]
        if not ready:
            return None
        ready.sort(key=lambda j: (j.priority, j.created_at))
        return ready[0]

    def get_job(self, job_id: str) -> Optional[PublishJob]:
        return self._jobs.get(job_id)

    def remove(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status in ("pending", "scheduled"):
            job.status = "cancelled"
            return True
        return False

    def count_by_status(self, status: str) -> int:
        return sum(1 for j in self._jobs.values() if j.status == status)

    def clear_completed(self) -> int:
        """Remove completed/failed jobs from queue."""
        to_remove = [jid for jid, j in self._jobs.items() if j.status in ("completed", "dead")]
        for jid in to_remove:
            del self._jobs[jid]
        self._jobs = {k: v for k, v in self._jobs.items() if v.status not in ("completed", "dead")}
        return len(to_remove)

    @property
    def size(self) -> int:
        return len(self._jobs)

    @property
    def is_full(self) -> bool:
        return len(self._jobs) >= self._max_size

    @property
    def enqueue_count(self) -> int:
        return self._enqueue_count

    @property
    def dequeue_count(self) -> int:
        return self._dequeue_count
