"""incremental_backup.py — Incremental backup support."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class IncrementalBackup:
    """Tracks incremental changes since last backup."""
    __slots__ = ("backup_id", "parent_id", "changes", "created_at", "size_bytes", "status")
    _counter = 0

    def __init__(self, parent_id: int = 0) -> None:
        IncrementalBackup._counter += 1
        self.backup_id: int = IncrementalBackup._counter
        self.parent_id = parent_id
        self.changes: List[Dict[str, Any]] = []
        self.created_at: float = time.time()
        self.size_bytes: int = 0
        self.status: str = "completed"


class IncrementalBackupManager:
    """Manages incremental backups."""

    def __init__(self) -> None:
        self._backups: Dict[int, IncrementalBackup] = {}

    def create(self, parent_id: int = 0, changes: List[Dict[str, Any]] = None) -> IncrementalBackup:
        backup = IncrementalBackup(parent_id)
        backup.changes = changes or []
        self._backups[backup.backup_id] = backup
        return backup

    def get_chain(self, backup_id: int) -> List[IncrementalBackup]:
        chain = []
        current = self._backups.get(backup_id)
        while current:
            chain.append(current)
            current = self._backups.get(current.parent_id)
        return chain

    def get_all(self) -> List[IncrementalBackup]:
        return list(self._backups.values())

    def stats(self) -> Dict[str, Any]:
        return {"backups": len(self._backups)}
