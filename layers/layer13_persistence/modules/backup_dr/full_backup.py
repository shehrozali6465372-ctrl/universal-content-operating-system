"""full_backup.py — Full backup management."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class FullBackup:
    """Full backup snapshot."""
    __slots__ = ("backup_id", "name", "size_bytes", "tables", "created_at", "status")
    _counter = 0

    def __init__(self, name: str = "") -> None:
        FullBackup._counter += 1
        self.backup_id: int = FullBackup._counter
        self.name = name or f"full_backup_{self.backup_id}"
        self.size_bytes: int = 0
        self.tables: List[str] = []
        self.created_at: float = time.time()
        self.status: str = "completed"


class FullBackupManager:
    """Manages full backups."""

    def __init__(self, max_backups: int = 10) -> None:
        self._backups: List[FullBackup] = []
        self._max = max_backups

    def create(self, name: str = "", tables: List[str] = None) -> FullBackup:
        backup = FullBackup(name)
        if tables:
            backup.tables = tables
        self._backups.append(backup)
        if len(self._backups) > self._max:
            self._backups = self._backups[-self._max:]
        return backup

    def get_latest(self) -> FullBackup:
        return self._backups[-1] if self._backups else None

    def get_all(self) -> List[FullBackup]:
        return list(self._backups)

    def stats(self) -> Dict[str, Any]:
        return {"backups": len(self._backups), "max": self._max}
