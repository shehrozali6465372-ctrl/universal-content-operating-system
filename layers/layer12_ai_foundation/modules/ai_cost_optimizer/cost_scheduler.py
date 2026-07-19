"""CostScheduler — schedule cost optimization tasks."""
from __future__ import annotations
import time
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class CostJob:
    job_id: str; task: str; priority: int = 5
    created_at: float = field(default_factory=time.time)
    status: str = "pending"

class CostScheduler:
    def __init__(self) -> None:
        self._queue: List[CostJob] = []; self._next_id = 0
    def schedule(self, task: str, priority: int = 5) -> str:
        self._next_id += 1
        job = CostJob(job_id=f"cost-{self._next_id}", task=task, priority=priority)
        self._queue.append(job); self._queue.sort(key=lambda j: j.priority)
        return job.job_id
    def get_next(self) -> Optional[CostJob]:
        for job in self._queue:
            if job.status == "pending": job.status = "running"; return job
        return None
    def complete(self, job_id: str) -> bool:
        for job in self._queue:
            if job.job_id == job_id:
                job.status = "completed"; self._queue = [j for j in self._queue if j.job_id != job_id]; return True
        return False
    def queue_size(self) -> int:
        return len([j for j in self._queue if j.status == "pending"])
