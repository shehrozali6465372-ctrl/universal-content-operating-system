"""Retry Strategy — Configurable retry policies with backoff."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class RetryPolicy:
    """Configuration for retry behavior."""

    __slots__ = ("max_retries", "base_delay", "max_delay", "backoff_factor", "jitter")

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "backoff_factor": self.backoff_factor,
            "jitter": self.jitter,
        }


POLICY_EAGER = RetryPolicy(max_retries=1, base_delay=0.1, backoff_factor=1.0, jitter=False)
POLICY_NORMAL = RetryPolicy(max_retries=3, base_delay=1.0, backoff_factor=2.0)
POLICY_PATIENT = RetryPolicy(max_retries=5, base_delay=2.0, backoff_factor=3.0, max_delay=600.0)
POLICY_RATE_LIMIT = RetryPolicy(max_retries=5, base_delay=10.0, backoff_factor=2.0, max_delay=300.0)


class RetryAttempt:
    """Record of a single retry attempt."""

    __slots__ = ("attempt", "delay", "timestamp", "error", "success")

    def __init__(self, attempt: int, delay: float) -> None:
        self.attempt = attempt
        self.delay = delay
        self.timestamp: float = time.time()
        self.error: str = ""
        self.success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt": self.attempt,
            "delay": self.delay,
            "timestamp": self.timestamp,
            "error": self.error,
            "success": self.success,
        }


class RetryStrategy:
    """Execute retries with configurable strategy."""

    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self.policy = policy or POLICY_NORMAL
        self._attempts_history: List[RetryAttempt] = []

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.policy.max_retries

    def get_delay(self, attempt: int) -> float:
        delay = self.policy.base_delay * (self.policy.backoff_factor ** attempt)
        delay = min(delay, self.policy.max_delay)
        if self.policy.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        return delay

    def get_total_delay(self, max_attempts: int) -> float:
        return sum(self.get_delay(i) for i in range(min(max_attempts, self.policy.max_retries)))

    def record_attempt(self, attempt: int, error: str = "", success: bool = False) -> RetryAttempt:
        rec = RetryAttempt(attempt, self.get_delay(attempt))
        rec.error = error[:200]
        rec.success = success
        self._attempts_history.append(rec)
        return rec

    def get_history(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._attempts_history]

    def reset_history(self) -> None:
        self._attempts_history.clear()

    @property
    def total_attempts(self) -> int:
        return len(self._attempts_history)
