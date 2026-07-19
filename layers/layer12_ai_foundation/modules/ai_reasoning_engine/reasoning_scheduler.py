"""ReasoningScheduler — schedule reasoning operations."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ReasoningJob:
    job_id: str
    problem: str
    reasoning_type: str
    priority: int = 5
    created_at: float = field(default_factory=time.time)
    status: str = "pending"


class ReasoningScheduler:
    """Schedule and manage reasoning operations."""

    def __init__(self) -> None:
        self._queue: List[ReasoningJob] = []
        self._completed: List[ReasoningJob] = []
        self._next_id = 0

    def schedule(self, problem: str, reasoning_type: str = "logical",
                 priority: int = 5) -> str:
        self._next_id += 1
        job = ReasoningJob(job_id=f"reason-{self._next_id}",
                           problem=problem, reasoning_type=reasoning_type,
                           priority=priority)
        self._queue.append(job)
        self._queue.sort(key=lambda j: j.priority)
        return job.job_id

    def get_next(self) -> Optional[ReasoningJob]:
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

    def queue_size(self) -> int:
        return len([j for j in self._queue if j.status == "pending"])

    def get_queue(self) -> List[Dict[str, Any]]:
        return [{"job_id": j.job_id, "type": j.reasoning_type,
                 "priority": j.priority, "status": j.status} for j in self._queue]
