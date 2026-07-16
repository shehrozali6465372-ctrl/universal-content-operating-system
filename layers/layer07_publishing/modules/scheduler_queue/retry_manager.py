"""Retry Manager — Handle job retries with exponential backoff."""
from __future__ import annotations
from typing import Dict, List, Optional

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class RetryPolicy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 300.0, backoff_factor: float = 2.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


class RetryManager:
    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self.policy = policy or RetryPolicy()
        self._retry_count = 0

    def should_retry(self, job: PublishJob) -> bool:
        return job.attempts < job.max_retries

    def get_next_delay(self, job: PublishJob) -> float:
        return self.policy.get_delay(job.attempts)

    def record_failure(self, job: PublishJob, error: str = "") -> None:
        job.attempts += 1
        job.last_error = error[:200]
        self._retry_count += 1

    def get_retry_history(self, jobs: List[PublishJob]) -> List[Dict]:
        return [
            {"job_id": j.job_id, "attempts": j.attempts, "last_error": j.last_error[:100]}
            for j in jobs if j.attempts > 0
        ]

    @property
    def retry_count(self) -> int:
        return self._retry_count
