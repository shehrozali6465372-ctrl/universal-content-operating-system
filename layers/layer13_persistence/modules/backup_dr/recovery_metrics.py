"""recovery_metrics.py — Recovery metrics."""
from __future__ import annotations
from typing import Any, Dict


class RecoveryMetrics:
    """Tracks recovery metrics."""

    def __init__(self) -> None:
        self._backups: int = 0
        self._restores: int = 0
        self._failovers: int = 0
        self._successful: int = 0
        self._failed: int = 0

    def record_backup(self, success: bool = True) -> None:
        self._backups += 1
        if success:
            self._successful += 1
        else:
            self._failed += 1

    def record_restore(self, success: bool = True) -> None:
        self._restores += 1

    def record_failover(self) -> None:
        self._failovers += 1

    def to_dict(self) -> Dict[str, Any]:
        return {"backups": self._backups, "restores": self._restores,
                "failovers": self._failovers, "successful": self._successful,
                "failed": self._failed}
