"""backup_coordinator.py — Backup coordination."""
from __future__ import annotations
import time
from typing import Any, Dict


class BackupCoordinator:
    """Coordinates backups across all stores."""

    def __init__(self) -> None:
        self._backup_schedules: Dict[str, float] = {}
        self._last_backups: Dict[str, float] = {}
        self._backup_count: int = 0

    def schedule_backup(self, store_name: str, interval_seconds: float) -> None:
        self._backup_schedules[store_name] = interval_seconds

    def trigger_backup(self, store_name: str) -> bool:
        self._last_backups[store_name] = time.time()
        self._backup_count += 1
        return True

    def get_schedule(self, store_name: str) -> float:
        return self._backup_schedules.get(store_name, 0.0)

    def get_last_backup(self, store_name: str) -> float:
        return self._last_backups.get(store_name, 0.0)

    def stats(self) -> Dict[str, Any]:
        return {"scheduled": len(self._backup_schedules), "total_backups": self._backup_count}
