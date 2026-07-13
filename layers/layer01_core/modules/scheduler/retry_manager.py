"""
Retry Manager Module
Layer 1: Core System — Module 7

Manages retries with exponential backoff for failed tasks.
"""

import time
from typing import Dict, Any
from datetime import datetime, timezone


class RetryManager:
    """Exponential backoff retry management."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 300.0):
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._retries: Dict[str, Dict] = {}

    def record_failure(self, task_id: str) -> Dict[str, Any]:
        """Record a failure for a task. Returns delay info."""
        now = time.time()
        if task_id not in self._retries:
            self._retries[task_id] = {"attempts": 0, "last_failure": now}

        info = self._retries[task_id]
        info["attempts"] += 1
        info["last_failure"] = now

        delay = min(self._base_delay * (2 ** (info["attempts"] - 1)), self._max_delay)
        return {
            "attempt": info["attempts"],
            "delay_seconds": delay,
            "next_retry_at": datetime.fromtimestamp(now + delay, tz=timezone.utc).isoformat(),
        }

    def record_success(self, task_id: str) -> None:
        """Reset retry count on success."""
        self._retries.pop(task_id, None)

    def should_retry(self, task_id: str, max_retries: int = 3) -> bool:
        """Check if a task should be retried."""
        info = self._retries.get(task_id)
        if not info:
            return True
        return info["attempts"] < max_retries

    def get_retry_count(self, task_id: str) -> int:
        info = self._retries.get(task_id)
        return info["attempts"] if info else 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "tasks_with_retries": len(self._retries),
            "total_retry_count": sum(v["attempts"] for v in self._retries.values()),
        }

    def clear(self) -> None:
        self._retries.clear()
