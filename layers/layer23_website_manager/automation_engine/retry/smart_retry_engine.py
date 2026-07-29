"""SmartRetryEngine — Intelligent retry with exponential backoff."""
from __future__ import annotations
import time
import random
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import RetryPolicy


class SmartRetryEngine:
    """Manage retry logic with exponential backoff."""

    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self._policy: RetryPolicy = policy or RetryPolicy()
        self._retry_history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()

    @property
    def policy(self) -> RetryPolicy:
        return self._policy

    @policy.setter
    def policy(self, p: RetryPolicy) -> None:
        self._policy = p

    def should_retry(self, attempt: int, error: str = "") -> bool:
        if attempt >= self._policy.max_retries:
            return False
        if self._policy.retry_on_errors:
            return any(e in error for e in self._policy.retry_on_errors)
        return True

    def calculate_delay(self, attempt: int) -> float:
        delay = self._policy.base_delay * (self._policy.backoff_factor ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, self._policy.max_delay)

    def record_retry(self, task_id: str, attempt: int, error: str = "") -> Dict[str, Any]:
        entry = {
            "task_id": task_id,
            "attempt": attempt,
            "delay_seconds": round(self.calculate_delay(attempt), 1),
            "error": error,
            "timestamp": time.time(),
        }
        with self._lock:
            if task_id not in self._retry_history:
                self._retry_history[task_id] = []
            self._retry_history[task_id].append(entry)
        return entry

    def get_history(self, task_id: str) -> List[Dict[str, Any]]:
        return self._retry_history.get(task_id, [])

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = sum(len(h) for h in self._retry_history.values())
            return {
                "total_retries": total,
                "tracked_tasks": len(self._retry_history),
                "max_retries": self._policy.max_retries,
                "base_delay": self._policy.base_delay,
                "backoff_factor": self._policy.backoff_factor,
            }
