"""RetryEngine — automatic retry with exponential backoff."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


class RetryConfig:
    __slots__ = ("max_retries", "base_delay", "max_delay", "exponential_base",
                 "jitter", "retry_on", "metadata")

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True, retry_on: Optional[tuple] = None) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or (Exception,)
        self.metadata: Dict[str, Any] = {}


class RetryResult:
    __slots__ = ("attempt_id", "success", "result", "error", "attempts",
                 "total_duration_ms", "delays", "metadata")

    def __init__(self) -> None:
        self.attempt_id = str(uuid.uuid4())[:12]
        self.success = False
        self.result: Any = None
        self.error: Optional[str] = None
        self.attempts = 0
        self.total_duration_ms: float = 0.0
        self.delays: List[float] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"attempt_id": self.attempt_id, "success": self.success,
                "attempts": self.attempts, "total_duration_ms": round(self.total_duration_ms, 2),
                "delays": [round(d, 3) for d in self.delays]}


class RetryEngine:
    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        import random
        delay = min(config.base_delay * (config.exponential_base ** attempt), config.max_delay)
        if config.jitter:
            delay *= (0.5 + random.random())
        return delay

    async def execute_with_retry(self, coro_fn: Callable, config: Optional[RetryConfig] = None,
                                 *args: Any, **kwargs: Any) -> RetryResult:
        config = config or RetryConfig()
        result = RetryResult()
        start = time.time()
        for attempt in range(config.max_retries + 1):
            result.attempts = attempt + 1
            try:
                coro = coro_fn(*args, **kwargs)
                if asyncio.iscoroutine(coro):
                    result.result = await coro
                else:
                    result.result = coro
                result.success = True
                break
            except config.retry_on as exc:
                result.error = str(exc)
                if attempt < config.max_retries:
                    delay = self._calculate_delay(attempt, config)
                    result.delays.append(delay)
                    await asyncio.sleep(delay)
        result.total_duration_ms = (time.time() - start) * 1000
        self._history.append(result.to_dict())
        return result

    def execute_sync(self, func: Callable, config: Optional[RetryConfig] = None,
                     *args: Any, **kwargs: Any) -> RetryResult:
        config = config or RetryConfig()
        result = RetryResult()
        start = time.time()
        for attempt in range(config.max_retries + 1):
            result.attempts = attempt + 1
            try:
                result.result = func(*args, **kwargs)
                result.success = True
                break
            except config.retry_on as exc:
                result.error = str(exc)
                if attempt < config.max_retries:
                    import time as _time
                    delay = self._calculate_delay(attempt, config)
                    result.delays.append(delay)
                    _time.sleep(delay)
        result.total_duration_ms = (time.time() - start) * 1000
        self._history.append(result.to_dict())
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def stats(self) -> Dict[str, Any]:
        total = len(self._history)
        success = sum(1 for h in self._history if h.get("success"))
        return {"total": total, "success": success, "failed": total - success}
