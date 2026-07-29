"""AutoScalingEngine — Automatically scale workers based on load."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import ScalingPolicy


class AutoScalingEngine:
    """Auto-scale workers based on metrics."""

    def __init__(self, policy: Optional[ScalingPolicy] = None) -> None:
        self._policy: ScalingPolicy = policy or ScalingPolicy()
        self._last_scale_up: float = 0.0
        self._last_scale_down: float = 0.0
        self._total_scale_ups: int = 0
        self._total_scale_downs: int = 0
        self._lock = threading.RLock()

    @property
    def policy(self) -> ScalingPolicy:
        return self._policy

    @policy.setter
    def policy(self, p: ScalingPolicy) -> None:
        self._policy = p

    def should_scale_up(self, current_workers: int, cpu: float = 0.0,
                        queue_size: int = 0) -> bool:
        if current_workers >= self._policy.max_workers:
            return False
        if time.time() - self._last_scale_up < self._policy.cooldown:
            return False
        if cpu > self._policy.cpu_threshold:
            return True
        if queue_size > self._policy.queue_threshold:
            return True
        return False

    def should_scale_down(self, current_workers: int, cpu: float = 0.0,
                           queue_size: int = 0) -> bool:
        if current_workers <= self._policy.min_workers:
            return False
        if time.time() - self._last_scale_down < self._policy.cooldown:
            return False
        if cpu < self._policy.cpu_threshold * 0.5 and queue_size == 0:
            return True
        return False

    def scale_up(self, current: int) -> int:
        with self._lock:
            new_count = min(current + self._policy.scale_up_by,
                            self._policy.max_workers)
            self._last_scale_up = time.time()
            self._total_scale_ups += 1
        return new_count

    def scale_down(self, current: int) -> int:
        with self._lock:
            new_count = max(current - self._policy.scale_down_by,
                            self._policy.min_workers)
            self._last_scale_down = time.time()
            self._total_scale_downs += 1
        return new_count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "min_workers": self._policy.min_workers,
                "max_workers": self._policy.max_workers,
                "cpu_threshold": self._policy.cpu_threshold,
                "queue_threshold": self._policy.queue_threshold,
                "total_scale_ups": self._total_scale_ups,
                "total_scale_downs": self._total_scale_downs,
                "cooldown": self._policy.cooldown,
            }
