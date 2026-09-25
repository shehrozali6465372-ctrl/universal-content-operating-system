"""Validated retry policy with bounded exponential backoff."""
from __future__ import annotations

import math
from typing import Any, Dict


class RetryPolicy:
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0) -> None:
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        if isinstance(delay, bool) or not isinstance(delay, (int, float)) or delay < 0:
            raise ValueError("delay must be >= 0")
        if isinstance(backoff, bool) or not isinstance(backoff, (int, float)) or backoff < 1:
            raise ValueError("backoff must be >= 1")
        self.max_retries = max_retries
        self.delay = float(delay)
        self.backoff = float(backoff)

    def get_delay(self, attempt: int) -> float:
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 0:
            raise ValueError("attempt must be a non-negative integer")
        value = self.delay * (self.backoff ** attempt)
        if not math.isfinite(value):
            raise OverflowError("retry delay is not finite")
        return value

    def can_retry(self, attempt: int) -> bool:
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 0:
            raise ValueError("attempt must be a non-negative integer")
        return attempt < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "delay": self.delay,
            "backoff": self.backoff,
        }
