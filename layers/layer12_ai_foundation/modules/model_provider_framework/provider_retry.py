"""provider_retry.py — Retry logic with exponential backoff."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict


class ProviderRetry:
    """Handles retry logic for failed provider calls."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 30.0, exponential: float = 2.0) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._exponential = exponential
        self._retry_counts: Dict[str, int] = {}

    def get_delay(self, attempt: int) -> float:
        delay = self._base_delay * (self._exponential ** attempt)
        return min(delay, self._max_delay)

    def should_retry(self, provider: str, attempt: int, error: str = "") -> bool:
        if attempt >= self._max_retries:
            return False
        retryable = ["timeout", "rate_limit", "503", "502", "429", "connection"]
        return any(r in str(error).lower() for r in retryable)

    def execute_with_retry(self, func: Callable, provider: str,
                           *args: Any, **kwargs: Any) -> Any:
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self._retry_counts[provider] = 0
                return result
            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    time.sleep(self.get_delay(attempt))
        raise last_error

    def get_retry_count(self, provider: str) -> int:
        return self._retry_counts.get(provider, 0)

    def reset(self, provider: str = "") -> None:
        if provider:
            self._retry_counts.pop(provider, None)
        else:
            self._retry_counts.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"max_retries": self._max_retries, "base_delay": self._base_delay,
                "retry_counts": dict(self._retry_counts)}
