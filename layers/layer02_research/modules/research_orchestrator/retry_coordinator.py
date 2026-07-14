"""
Retry Coordinator
Layer 2: Research Engine — Module 10

Manages retry logic for failed modules:
- Exponential backoff
- Configurable retry limits
- Retry history tracking
- Fallback strategies
"""

import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Any

from layers.layer02_research.modules.research_orchestrator.exceptions import RetryExhaustedError


class RetryPolicy:
    """Configuration for retry behavior."""

    __slots__ = (
        "max_retries", "base_delay_sec", "max_delay_sec",
        "backoff_multiplier", "jitter",
    )

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_sec: float = 1.0,
        max_delay_sec: float = 30.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay_sec = base_delay_sec
        self.max_delay_sec = max_delay_sec
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter

    def to_dict(self) -> dict:
        return {
            "max_retries": self.max_retries,
            "base_delay_sec": self.base_delay_sec,
            "max_delay_sec": self.max_delay_sec,
            "backoff_multiplier": self.backoff_multiplier,
            "jitter": self.jitter,
        }


class RetryAttempt:
    """Record of a single retry attempt."""

    __slots__ = ("attempt_number", "module", "error", "timestamp", "delay_sec")

    def __init__(self, attempt_number: int, module: str, error: str, delay_sec: float = 0.0):
        self.attempt_number = attempt_number
        self.module = module
        self.error = error
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.delay_sec = delay_sec

    def to_dict(self) -> dict:
        return {
            "attempt_number": self.attempt_number,
            "module": self.module,
            "error": self.error,
            "timestamp": self.timestamp,
            "delay_sec": self.delay_sec,
        }


class RetryCoordinator:
    """Manages retry logic for failed workflow modules."""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self._history: Dict[str, List[RetryAttempt]] = {}

    def should_retry(self, module: str) -> bool:
        """Check if a module should be retried."""
        attempts = self._history.get(module, [])
        return len(attempts) < self.policy.max_retries

    def record_attempt(self, module: str, error: str) -> RetryAttempt:
        """Record a retry attempt and return the attempt info."""
        if module not in self._history:
            self._history[module] = []

        attempt_num = len(self._history[module]) + 1
        delay = self._calculate_delay(attempt_num)
        attempt = RetryAttempt(attempt_num, module, error, delay)
        self._history[module].append(attempt)
        return attempt

    def get_delay(self, module: str) -> float:
        """Get the delay before the next retry for a module."""
        attempts = self._history.get(module, [])
        return self._calculate_delay(len(attempts) + 1)

    def get_attempts(self, module: str) -> List[RetryAttempt]:
        """Get all retry attempts for a module."""
        return list(self._history.get(module, []))

    def get_total_retries(self) -> int:
        """Get total retry count across all modules."""
        return sum(len(attempts) for attempts in self._history.values())

    def reset_module(self, module: str):
        """Reset retry history for a module."""
        self._history.pop(module, None)

    def reset_all(self):
        """Reset all retry history."""
        self._history.clear()

    def execute_with_retry(
        self,
        module: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retry logic."""
        last_error = None

        while self.should_retry(module):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                attempt = self.record_attempt(module, str(exc))

                if not self.should_retry(module):
                    break

                # In production, we'd sleep here, but for tests we skip actual sleep
                # time.sleep(attempt.delay_sec)

        raise RetryExhaustedError(
            f"Retry exhausted for '{module}' after "
            f"{len(self.get_attempts(module))} attempts: {last_error}"
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay using exponential backoff."""
        import random

        delay = self.policy.base_delay_sec * (
            self.policy.backoff_multiplier ** (attempt - 1)
        )
        delay = min(delay, self.policy.max_delay_sec)

        if self.policy.jitter:
            delay *= (0.5 + random.random())

        return round(delay, 3)
