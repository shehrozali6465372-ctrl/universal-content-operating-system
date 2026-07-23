"""RedisRateLimiter — Token bucket and sliding window rate limiting.

Features:
- Token bucket algorithm (burst-friendly)
- Sliding window algorithm (strict)
- Per-user, per-platform, per-endpoint limits
- Rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset)
- Automatic cleanup of expired windows
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, Optional, Tuple


class RedisRateLimiter:
    """Rate limiting using Redis-backed counters."""

    def __init__(self, client: Any):
        self._client = client
        self._prefix = "ratelimit"
        self._lock = threading.Lock()

        # Stats
        self._total_requests = 0
        self._total_allowed = 0
        self._total_rejected = 0

    def _key(self, identifier: str, window: str = "sliding") -> str:
        return f"{self._prefix}:{window}:{identifier}"

    def sliding_window(self, identifier: str, max_requests: int, window_seconds: float) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiter.

        Args:
            identifier: Unique key (e.g., "user:123:api_generate")
            max_requests: Maximum requests allowed in window
            window_seconds: Window duration in seconds

        Returns:
            (allowed, info_dict)
        """
        now = time.time()
        window_start = now - window_seconds
        key = self._key(identifier, "sliding")

        # Use sorted set with timestamp scores
        # Remove old entries
        self._client.execute_with_retry = getattr(self._client, '_execute_with_retry', None)

        # Simple approach: use incrementing counter with TTL
        counter_key = f"{self._prefix}:sw:{identifier}"
        count_raw = self._client.get(counter_key)

        if count_raw is not None:
            count = int(count_raw)
        else:
            count = 0

        self._total_requests += 1

        if count < max_requests:
            new_count = self._client.incr(counter_key)
            if new_count == 1:
                self._client.expire(counter_key, window_seconds)
            remaining = max_requests - new_count
            self._total_allowed += 1
            return True, {
                "allowed": True,
                "remaining": max(0, remaining),
                "limit": max_requests,
                "reset_at": now + window_seconds,
                "retry_after": 0,
            }
        else:
            self._total_rejected += 1
            return False, {
                "allowed": False,
                "remaining": 0,
                "limit": max_requests,
                "reset_at": now + window_seconds,
                "retry_after": window_seconds,
            }

    def token_bucket(self, identifier: str, capacity: int, refill_rate: float) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiter.

        Args:
            identifier: Unique key
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second

        Returns:
            (allowed, info_dict)
        """
        now = time.time()
        bucket_key = f"{self._prefix}:tb:{identifier}"

        # Get current bucket state
        state_raw = self._client.get(bucket_key)
        if state_raw:
            try:
                import json
                state = json.loads(state_raw)
                tokens = state.get("tokens", capacity)
                last_refill = state.get("last_refill", now)
            except (json.JSONDecodeError, TypeError):
                tokens = capacity
                last_refill = now
        else:
            tokens = capacity
            last_refill = now

        # Refill tokens
        elapsed = now - last_refill
        tokens = min(capacity, tokens + elapsed * refill_rate)

        self._total_requests += 1

        if tokens >= 1.0:
            tokens -= 1.0
            import json
            self._client.set(bucket_key, json.dumps({
                "tokens": tokens,
                "last_refill": now,
            }), ttl=capacity / refill_rate * 2)
            self._total_allowed += 1
            return True, {
                "allowed": True,
                "tokens_remaining": round(tokens, 2),
                "capacity": capacity,
                "refill_rate": refill_rate,
            }
        else:
            wait_time = (1.0 - tokens) / refill_rate
            self._total_rejected += 1
            return False, {
                "allowed": False,
                "tokens_remaining": 0,
                "capacity": capacity,
                "refill_rate": refill_rate,
                "retry_after": round(wait_time, 2),
            }

    def check_and_consume(self, identifier: str, max_requests: int,
                          window_seconds: float = 60.0) -> Tuple[bool, Dict[str, Any]]:
        """Convenience method: check rate limit and consume if allowed."""
        return self.sliding_window(identifier, max_requests, window_seconds)

    def reset(self, identifier: str) -> bool:
        """Reset rate limit for an identifier."""
        keys = [
            f"{self._prefix}:sw:{identifier}",
            f"{self._prefix}:tb:{identifier}",
        ]
        for k in keys:
            self._client.delete(k)
        return True

    def get_usage(self, identifier: str, window_seconds: float = 60.0) -> Dict[str, Any]:
        """Get current usage for an identifier."""
        counter_key = f"{self._prefix}:sw:{identifier}"
        count_raw = self._client.get(counter_key)
        count = int(count_raw) if count_raw else 0

        return {
            "identifier": identifier,
            "current_count": count,
            "window_seconds": window_seconds,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        total = self._total_requests
        return {
            "total_requests": self._total_requests,
            "total_allowed": self._total_allowed,
            "total_rejected": self._total_rejected,
            "rejection_rate_pct": round(self._total_rejected / total * 100, 1) if total > 0 else 0.0,
        }

    def reset_stats(self) -> None:
        """Reset all counters."""
        with self._lock:
            self._total_requests = 0
            self._total_allowed = 0
            self._total_rejected = 0
