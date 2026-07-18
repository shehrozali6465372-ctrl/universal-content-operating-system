"""retry_policy.py — Database retry policies."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict


class RetryPolicy:
    """Configurable retry policy for database operations."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 30.0, backoff: float = 2.0) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._backoff = backoff
        self._retry_count: int = 0

    def get_delay(self, attempt: int) -> float:
        delay = self._base_delay * (self._backoff ** attempt)
        return min(delay, self._max_delay)

    def should_retry(self, attempt: int, error: Exception = None) -> bool:
        return attempt < self._max_retries

    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    time.sleep(self.get_delay(attempt))
                    self._retry_count += 1
        raise last_error

    def get_retry_count(self) -> int:
        return self._retry_count

    def reset(self) -> None:
        self._retry_count = 0

    def stats(self) -> Dict[str, Any]:
        return {"max_retries": self._max_retries, "retries_used": self._retry_count}
