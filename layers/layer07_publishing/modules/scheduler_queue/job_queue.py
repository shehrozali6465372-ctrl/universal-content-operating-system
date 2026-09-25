"""Job Queue — thread-safe priority queue for publishing jobs."""
from __future__ import annotations

import threading
from typing import Dict, List, Optional

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class JobQueue:
    """Thread-safe priority queue with duplicate-job protection."""

    def __init__(self, max_size: int = 10000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be positive")
        self._max_size = max_size
        self._jobs: Dict[str, PublishJob] = {}
        self._enqueue_count = 0
        self._dequeue_count = 0
        self._lock = threading.RLock()

    def enqueue(self, job: PublishJob) -> bool:
        if not job.job_id:
            raise ValueError("job_id is required")
        with self._lock:
            if job.job_id in self._jobs or len(self._jobs) >= self._max_size:
                return False
            self._jobs[job.job_id] = job
            self._enqueue_count += 1
            return True

    def enqueue_batch(self, jobs: List[PublishJob]) -> int:
        return sum(1 for job in jobs if self.enqueue(job))

    def dequeue(self, platform: Optional[str] = None) -> Optional[PublishJob]:
        with self._lock:
            ready = [
                job for job in self._jobs.values()
                if job.is_ready() and (platform is None or job.platform == platform)
            ]
            if not ready:
                return None
            ready.sort(key=lambda job: (job.priority, job.created_at))
            job = ready[0]
            job.status = "running"
            self._dequeue_count += 1
            return job

    def dequeue_many(self, count: int, platform: Optional[str] = None) -> List[PublishJob]:
        if count < 0:
            raise ValueError("count must be non-negative")
        jobs: List[PublishJob] = []
        for _ in range(count):
            job = self.dequeue(platform)
            if job is None:
                break
            jobs.append(job)
        return jobs

    def peek(self, platform: Optional[str] = None) -> Optional[PublishJob]:
        with self._lock:
            ready = [
                job for job in self._jobs.values()
                if job.is_ready() and (platform is None or job.platform == platform)
            ]
            if not ready:
                return None
            return min(ready, key=lambda job: (job.priority, job.created_at))

    def get_job(self, job_id: str) -> Optional[PublishJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def remove(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status in ("pending", "scheduled"):
                job.status = "cancelled"
                return True
            return False

    def count_by_status(self, status: str) -> int:
        with self._lock:
            return sum(1 for job in self._jobs.values() if job.status == status)

    def clear_completed(self) -> int:
        with self._lock:
            removable = [
                job_id for job_id, job in self._jobs.items()
                if job.status in ("completed", "dead")
            ]
            for job_id in removable:
                del self._jobs[job_id]
            return len(removable)

    def snapshot(self) -> List[PublishJob]:
        with self._lock:
            return list(self._jobs.values())

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._jobs)

    @property
    def is_full(self) -> bool:
        with self._lock:
            return len(self._jobs) >= self._max_size

    @property
    def enqueue_count(self) -> int:
        return self._enqueue_count

    @property
    def dequeue_count(self) -> int:
        return self._dequeue_count
