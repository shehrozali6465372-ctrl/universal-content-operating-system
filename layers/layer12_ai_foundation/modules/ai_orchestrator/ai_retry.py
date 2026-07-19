"""AIRetry — retry logic for failed operations."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List

class AIRetry:
    def __init__(self, max_retries: int = 3, delay_ms: float = 100.0) -> None:
        self.max_retries = max_retries; self.delay_ms = delay_ms
        self._retry_log: List[Dict[str, Any]] = []
    def retry(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    self._retry_log.append({"attempt": attempt, "success": True})
                return result
            except Exception as exc:
                last_error = exc
                self._retry_log.append({"attempt": attempt, "success": False, "error": str(exc)})
                if attempt < self.max_retries:
                    time.sleep(self.delay_ms / 1000)
        raise last_error
    def get_log(self) -> List[Dict[str, Any]]: return list(self._retry_log)
