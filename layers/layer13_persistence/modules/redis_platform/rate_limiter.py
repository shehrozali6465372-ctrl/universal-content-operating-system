"""rate_limiter.py — Redis-based rate limiting."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RateLimiter:
    """Token bucket / sliding window rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._blocked: Dict[str, float] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if key in self._blocked and now < self._blocked[key]:
            return False
        self._requests.setdefault(key, [])
        cutoff = now - self._window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= self._max_requests:
            self._blocked[key] = now + self._window_seconds
            return False
        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        now = time.time()
        cutoff = now - self._window_seconds
        recent = [t for t in self._requests.get(key, []) if t > cutoff]
        return max(0, self._max_requests - len(recent))

    def reset(self, key: str = "") -> None:
        if key:
            self._requests.pop(key, None)
            self._blocked.pop(key, None)
        else:
            self._requests.clear()
            self._blocked.clear()

    def stats(self) -> Dict[str, Any]:
        return {"max_requests": self._max_requests,
                "window_seconds": self._window_seconds,
                "tracked_keys": len(self._requests)}
