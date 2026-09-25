"""provider_retry.py — bounded retry logic with explicit retryability."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict


class ProviderRetry:
    """Retry only transient provider failures with bounded exponential backoff."""

    _RETRYABLE_MARKERS = (
        "timeout",
        "rate_limit",
        "503",
        "502",
        "429",
        "connection",
        "temporarily unavailable",
        "service unavailable",
    )

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential: float = 2.0,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if base_delay < 0 or max_delay < 0:
            raise ValueError("retry delays must be >= 0")
        if exponential < 1:
            raise ValueError("exponential must be >= 1")
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._exponential = exponential
        self._retry_counts: Dict[str, int] = {}

    def get_delay(self, attempt: int) -> float:
        if attempt < 0:
            raise ValueError("attempt must be >= 0")
        return min(self._base_delay * (self._exponential ** attempt), self._max_delay)

    def should_retry(self, provider: str, attempt: int, error: str = "") -> bool:
        if attempt >= self._max_retries:
            return False
        return any(marker in str(error).lower() for marker in self._RETRYABLE_MARKERS)

    def execute_with_retry(
        self,
        func: Callable[..., Any],
        provider: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self._retry_counts[provider] = attempt
                return result
            except Exception as exc:
                last_error = exc
                if not self.should_retry(provider, attempt, str(exc)):
                    self._retry_counts[provider] = attempt
                    raise
                self._retry_counts[provider] = attempt + 1
                time.sleep(self.get_delay(attempt))
        assert last_error is not None
        raise last_error

    def get_retry_count(self, provider: str) -> int:
        return self._retry_counts.get(provider, 0)

    def reset(self, provider: str = "") -> None:
        if provider:
            self._retry_counts.pop(provider, None)
        else:
            self._retry_counts.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self._max_retries,
            "base_delay": self._base_delay,
            "max_delay": self._max_delay,
            "exponential": self._exponential,
            "retry_counts": dict(self._retry_counts),
        }
