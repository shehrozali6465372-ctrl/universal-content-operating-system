"""Recovery Metrics — Track recovery performance and failure statistics."""
from __future__ import annotations
from typing import Any, Dict, List


class RecoveryMetrics:
    """Collect and report recovery metrics."""

    def __init__(self) -> None:
        self._total_failures = 0
        self._recovered_count = 0
        self._failed_count = 0
        self._total_retries = 0
        self._total_recovery_time_ms = 0.0
        self._snapshots: List[Dict[str, Any]] = []

    def record_failure(self, recovered: bool, recovery_time_ms: float = 0.0) -> None:
        self._total_failures += 1
        if recovered:
            self._recovered_count += 1
        else:
            self._failed_count += 1
        self._total_recovery_time_ms += recovery_time_ms

    def record_retry(self) -> None:
        self._total_retries += 1

    def get_current(self) -> Dict[str, Any]:
        recovery_rate = self._recovered_count / max(1, self._total_failures)
        avg_recovery_time = (
            self._total_recovery_time_ms / max(1, self._total_failures)
        )
        return {
            "total_failures": self._total_failures,
            "recovered": self._recovered_count,
            "failed": self._failed_count,
            "recovery_rate": round(recovery_rate, 3),
            "total_retries": self._total_retries,
            "avg_recovery_time_ms": round(avg_recovery_time, 2),
        }

    def take_snapshot(self) -> Dict[str, Any]:
        snap = self.get_current()
        self._snapshots.append(snap)
        return snap

    def get_snapshots(self) -> List[Dict[str, Any]]:
        return list(self._snapshots)

    def reset(self) -> None:
        self._total_failures = 0
        self._recovered_count = 0
        self._failed_count = 0
        self._total_retries = 0
        self._total_recovery_time_ms = 0.0
