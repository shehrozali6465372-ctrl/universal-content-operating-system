"""Dead Letter Queue — Handle permanently failed jobs."""
from __future__ import annotations
import time
from typing import List, Optional

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class DeadLetterEntry:
    def __init__(self, job: PublishJob, failure_reason: str = "") -> None:
        self.job = job
        self.failure_reason = failure_reason
        self.timestamp = time.time()
        self.recovered = False

    def to_dict(self) -> dict:
        return {
            "job_id": self.job.job_id,
            "platform": self.job.platform,
            "failure_reason": self.failure_reason,
            "timestamp": self.timestamp,
            "attempts": self.job.attempts,
            "recovered": self.recovered,
        }


class DeadLetterQueue:
    def __init__(self) -> None:
        self._entries: List[DeadLetterEntry] = []

    def add(self, job: PublishJob, reason: str = "") -> DeadLetterEntry:
        job.status = "dead"
        entry = DeadLetterEntry(job, reason)
        self._entries.append(entry)
        return entry

    def list_entries(self, platform: Optional[str] = None) -> List[DeadLetterEntry]:
        if platform:
            return [e for e in self._entries if e.job.platform == platform]
        return list(self._entries)

    def recover(self, index: int) -> Optional[PublishJob]:
        if 0 <= index < len(self._entries):
            entry = self._entries[index]
            entry.recovered = True
            entry.job.status = "pending"
            entry.job.attempts = 0
            return entry.job
        return None

    def remove(self, index: int) -> bool:
        if 0 <= index < len(self._entries):
            self._entries.pop(index)
            return True
        return False

    @property
    def size(self) -> int:
        return len(self._entries)

    @property
    def recovered_count(self) -> int:
        return sum(1 for e in self._entries if e.recovered)
