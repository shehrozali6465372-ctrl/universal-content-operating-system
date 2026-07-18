"""BackupManager — Backup memory, settings, analytics, strategies."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

import itertools
_BM_COUNTER = itertools.count(1)


class BackupEntry:
    """A backup record."""

    __slots__ = ("backup_id", "backup_type", "description", "data",
                 "size_bytes", "created_at", "status")

    def __init__(self, backup_type: str = "", description: str = "") -> None:
        self.backup_id: str = f"bak_{next(_BM_COUNTER)}"
        self.backup_type = backup_type
        self.description = description
        self.data: Dict[str, Any] = {}
        self.size_bytes: int = 0
        self.created_at: float = time.time()
        self.status: str = "completed"


class BackupManager:
    """Create, list, restore, and delete backups of system data."""

    def __init__(self) -> None:
        self._backups: List[BackupEntry] = []

    def create(self, backup_type: str, data: Dict[str, Any],
               description: str = "") -> BackupEntry:
        entry = BackupEntry(backup_type, description)
        entry.data = dict(data)
        entry.size_bytes = len(str(data))
        self._backups.append(entry)
        return entry

    def restore(self, backup_id: str) -> Optional[Dict[str, Any]]:
        for backup in self._backups:
            if backup.backup_id == backup_id:
                return dict(backup.data)
        return None

    def delete(self, backup_id: str) -> bool:
        for i, backup in enumerate(self._backups):
            if backup.backup_id == backup_id:
                self._backups.pop(i)
                return True
        return False

    def get_recent(self, count: int = 5) -> List[BackupEntry]:
        return self._backups[-count:]

    def get_by_type(self, backup_type: str) -> List[BackupEntry]:
        return [b for b in self._backups if b.backup_type == backup_type]

    def get_total_size(self) -> int:
        return sum(b.size_bytes for b in self._backups)

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for b in self._backups:
            types[b.backup_type] = types.get(b.backup_type, 0) + 1
        return {"total_backups": len(self._backups), "total_size_bytes": self.get_total_size(),
                "by_type": types}
