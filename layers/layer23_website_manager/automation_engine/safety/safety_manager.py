"""SafetyManager — Prevent infinite loops, duplicates, rate limit violations."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import SafetyPolicy
from layers.layer23_website_manager.automation_engine.exceptions import SafetyError


class SafetyManager:
    """Enforce safety policies to prevent abuse."""

    def __init__(self, policy: Optional[SafetyPolicy] = None) -> None:
        self._policy: SafetyPolicy = policy or SafetyPolicy()
        self._execution_times: List[float] = []
        self._recent_actions: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
        self._violations: int = 0

    @property
    def policy(self) -> SafetyPolicy:
        return self._policy

    def check_rate_limit(self, action: str = "default") -> bool:
        now = time.time()
        with self._lock:
            times = self._recent_actions.setdefault(action, [])
            times = [t for t in times if now - t < 60]
            self._recent_actions[action] = times
            if len(times) >= self._policy.rate_limit_per_minute:
                self._violations += 1
                return False
            times.append(now)
        return True

    def check_concurrent(self, current: int) -> bool:
        if current >= self._policy.max_concurrent:
            self._violations += 1
            return False
        return True

    def check_daily_limit(self, today_count: int) -> bool:
        if today_count >= self._policy.max_daily_executions:
            self._violations += 1
            return False
        return True

    def check_interval(self, last_time: Optional[float]) -> bool:
        if last_time is None:
            return True
        if (time.time() - last_time) < self._policy.min_interval_seconds:
            self._violations += 1
            return False
        return True

    def check_blocked_hours(self) -> bool:
        current_hour = time.localtime().tm_hour
        return current_hour not in self._policy.blocked_hours

    def record_execution(self) -> None:
        with self._lock:
            self._execution_times.append(time.time())

    def get_daily_count(self) -> int:
        now = time.time()
        with self._lock:
            return sum(1 for t in self._execution_times if now - t < 86400)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "violations": self._violations,
                "daily_executions": self.get_daily_count(),
                "max_daily": self._policy.max_daily_executions,
                "max_concurrent": self._policy.max_concurrent,
                "rate_limit": self._policy.rate_limit_per_minute,
                "blocked_hours": self._policy.blocked_hours,
            }
