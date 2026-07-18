"""TaskTimeout — Timeout management for tasks."""
from __future__ import annotations
import time
class TaskTimeout:
    def __init__(self, timeout_seconds: float=300.0): self.timeout = timeout_seconds
    def is_expired(self, started_at: float) -> bool: return (time.time() - started_at) > self.timeout
    def remaining(self, started_at: float) -> float: return max(0.0, self.timeout - (time.time() - started_at))
