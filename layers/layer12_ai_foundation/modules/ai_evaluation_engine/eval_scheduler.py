"""EvalScheduler — schedule evaluation tasks."""
from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass, field
import time

@dataclass
class EvalJob:
    job_id: str; content: str; eval_types: list = field(default_factory=list)
    priority: int = 5; status: str = "pending"
    created_at: float = field(default_factory=time.time)

class EvalScheduler:
    def __init__(self) -> None:
        self._queue: List[EvalJob] = []; self._next_id = 0
    def schedule(self, content: str, eval_types: list | None = None, priority: int = 5) -> str:
        self._next_id += 1
        job = EvalJob(job_id=f"eval-{self._next_id}", content=content[:200],
                      eval_types=eval_types or ["quality"], priority=priority)
        self._queue.append(job); self._queue.sort(key=lambda j: j.priority); return job.job_id
    def get_next(self) -> Optional[EvalJob]:
        for j in self._queue:
            if j.status == "pending": j.status = "running"; return j
        return None
    def complete(self, job_id: str) -> bool:
        for j in self._queue:
            if j.job_id == job_id:
                j.status = "completed"; self._queue = [x for x in self._queue if x.job_id != job_id]; return True
        return False
    def queue_size(self) -> int: return len([j for j in self._queue if j.status == "pending"])
