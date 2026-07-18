"""redis_metrics.py — Redis metrics tracking."""
from __future__ import annotations
from typing import Any, Dict


class RedisMetrics:
    """Tracks Redis metrics."""

    def __init__(self) -> None:
        self._operations: int = 0
        self._errors: int = 0
        self._total_time_ms: float = 0.0
        self._by_command: Dict[str, int] = {}

    def record(self, command: str, latency_ms: float, success: bool = True) -> None:
        self._operations += 1
        self._total_time_ms += latency_ms
        self._by_command[command] = self._by_command.get(command, 0) + 1
        if not success:
            self._errors += 1

    def get_avg_latency(self) -> float:
        return self._total_time_ms / max(1, self._operations)

    def get_error_rate(self) -> float:
        return self._errors / max(1, self._operations)

    def reset(self) -> None:
        self._operations = 0
        self._errors = 0
        self._total_time_ms = 0.0
        self._by_command.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"operations": self._operations, "errors": self._errors,
                "avg_latency_ms": self.get_avg_latency(),
                "by_command": dict(self._by_command)}
