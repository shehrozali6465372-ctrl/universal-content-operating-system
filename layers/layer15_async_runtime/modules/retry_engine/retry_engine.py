"""Bounded retry engine with validated exponential backoff."""
from __future__ import annotations

import asyncio
import inspect
import random
import time
import uuid
from typing import Any, Callable


class RetryConfig:
    __slots__ = ("max_retries", "base_delay", "max_delay", "exponential_base",
                 "jitter", "retry_on", "metadata")

    def __init__(
        self, max_retries: int = 3, base_delay: float = 1.0,
        max_delay: float = 60.0, exponential_base: float = 2.0,
        jitter: bool = True, retry_on: tuple[type[BaseException], ...] | None = None,
    ) -> None:
        if max_retries < 0 or base_delay < 0 or max_delay < 0 or exponential_base < 1:
            raise ValueError("invalid retry configuration")
        if base_delay > max_delay:
            raise ValueError("base_delay cannot exceed max_delay")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or (Exception,)
        self.metadata: dict[str, Any] = {}

    def validate(self) -> None:
        if not self.retry_on:
            raise ValueError("retry_on cannot be empty")


class RetryResult:
    __slots__ = ("attempt_id", "success", "result", "error", "attempts",
                 "total_duration_ms", "delays", "metadata")

    def __init__(self) -> None:
        self.attempt_id = str(uuid.uuid4())
        self.success = False
        self.result: Any = None
        self.error: str | None = None
        self.attempts = 0
        self.total_duration_ms = 0.0
        self.delays: list[float] = []
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id, "success": self.success,
            "attempts": self.attempts, "total_duration_ms": round(self.total_duration_ms, 2),
            "delays": [round(d, 3) for d in self.delays],
            "error": self.error,
        }


class RetryEngine:
    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        delay = min(config.base_delay * config.exponential_base ** attempt, config.max_delay)
        return delay * (0.5 + random.random()) if config.jitter else delay

    async def execute_with_retry(
        self, coro_fn: Callable[..., Any], config: RetryConfig | None = None,
        *args: Any, **kwargs: Any,
    ) -> RetryResult:
        config = config or RetryConfig()
        config.validate()
        result = RetryResult()
        start = time.time()
        for attempt in range(config.max_retries + 1):
            result.attempts = attempt + 1
            try:
                value = coro_fn(*args, **kwargs)
                result.result = await value if inspect.isawaitable(value) else value
                result.success = True
                break
            except asyncio.CancelledError:
                raise
            except config.retry_on as exc:
                result.error = f"{type(exc).__name__}: {exc}"
                if attempt < config.max_retries:
                    delay = self._calculate_delay(attempt, config)
                    result.delays.append(delay)
                    await asyncio.sleep(delay)
        result.total_duration_ms = (time.time() - start) * 1000
        self._history.append(result.to_dict())
        return result

    def execute_sync(
        self, func: Callable[..., Any], config: RetryConfig | None = None,
        *args: Any, **kwargs: Any,
    ) -> RetryResult:
        config = config or RetryConfig()
        config.validate()
        result = RetryResult()
        start = time.time()
        for attempt in range(config.max_retries + 1):
            result.attempts = attempt + 1
            try:
                result.result = func(*args, **kwargs)
                result.success = True
                break
            except config.retry_on as exc:
                result.error = f"{type(exc).__name__}: {exc}"
                if attempt < config.max_retries:
                    delay = self._calculate_delay(attempt, config)
                    result.delays.append(delay)
                    time.sleep(delay)
        result.total_duration_ms = (time.time() - start) * 1000
        self._history.append(result.to_dict())
        return result

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def stats(self) -> dict[str, int]:
        total = len(self._history)
        success = sum(bool(h.get("success")) for h in self._history)
        return {"total": total, "success": success, "failed": total - success}
