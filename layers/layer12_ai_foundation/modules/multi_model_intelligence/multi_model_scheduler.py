"""MultiModelScheduler — schedule multi-model operations."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ScheduledJob:
    job_id: str
    prompt: str
    models: List[str]
    priority: int = 5
    created_at: float = field(default_factory=time.time)
    status: str = "pending"


class MultiModelScheduler:
    """Schedule and manage multi-model operations."""

    def __init__(self) -> None:
        self._queue: List[ScheduledJob] = []
        self._completed: List[ScheduledJob] = []
        self._next_id = 0

    def schedule(self, prompt: str, models: List[str],
                 priority: int = 5) -> str:
        self._next_id += 1
        job = ScheduledJob(job_id=f"mmjob-{self._next_id}",
                           prompt=prompt, models=models, priority=priority)
        self._queue.append(job)
        self._queue.sort(key=lambda j: j.priority)
        return job.job_id

    def get_next(self) -> Optional[ScheduledJob]:
        for job in self._queue:
            if job.status == "pending":
                job.status = "running"
                return job
        return None

    def complete(self, job_id: str, success: bool = True) -> bool:
        for job in self._queue:
            if job.job_id == job_id:
                job.status = "completed" if success else "failed"
                self._completed.append(job)
                self._queue = [j for j in self._queue if j.job_id != job_id]
                return True
        return False

    def cancel(self, job_id: str) -> bool:
        for i, job in enumerate(self._queue):
            if job.job_id == job_id:
                job.status = "cancelled"
                self._queue.pop(i)
                return True
        return False

    def queue_size(self) -> int:
        return len([j for j in self._queue if j.status == "pending"])

    def get_queue(self) -> List[Dict[str, Any]]:
        return [{"job_id": j.job_id, "priority": j.priority, "status": j.status}
                for j in self._queue]
