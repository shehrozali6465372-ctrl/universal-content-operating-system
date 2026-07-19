"""GovernanceScheduler — schedule governance checks."""
from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass, field
import time

@dataclass
class GovJob:
    job_id: str; task: str; priority: int = 5; status: str = "pending"
    created_at: float = field(default_factory=time.time)

class GovernanceScheduler:
    def __init__(self) -> None:
        self._queue: List[GovJob] = []; self._next_id = 0
    def schedule(self, task: str, priority: int = 5) -> str:
        self._next_id += 1
        job = GovJob(job_id=f"gov-{self._next_id}", task=task, priority=priority)
        self._queue.append(job); return job.job_id
    def get_next(self) -> Optional[GovJob]:
        for j in self._queue:
            if j.status == "pending": j.status = "running"; return j
        return None
    def complete(self, job_id: str) -> bool:
        for j in self._queue:
            if j.job_id == job_id:
                j.status = "completed"; self._queue = [x for x in self._queue if x.job_id != job_id]; return True
        return False
    def queue_size(self) -> int: return len([j for j in self._queue if j.status == "pending"])
