"""TaskRetry — Retry logic for failed tasks."""
from __future__ import annotations
from typing import Any, Dict
class RetryPolicy:
    def __init__(self, max_retries: int=3, delay: float=1.0, backoff: float=2.0):
        self.max_retries = max_retries; self.delay = delay; self.backoff = backoff
    def get_delay(self, attempt: int) -> float: return self.delay * (self.backoff ** attempt)
    def can_retry(self, attempt: int) -> bool: return attempt < self.max_retries
    def to_dict(self) -> Dict[str, Any]: return {"max_retries": self.max_retries, "delay": self.delay, "backoff": self.backoff}
