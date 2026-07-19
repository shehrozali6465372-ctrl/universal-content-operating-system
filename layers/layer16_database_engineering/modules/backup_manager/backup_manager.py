"""BackupManager — database backup and restore operations."""
from __future__ import annotations
import time
import uuid
import copy
from typing import Any, Dict, List, Optional


class BackupEntry:
    __slots__ = ("backup_id", "name", "data", "created_at", "size_bytes", "metadata")

    def __init__(self, name: str, data: Dict[str, Any]) -> None:
        self.backup_id = str(uuid.uuid4())[:12]
        self.name = name
        self.data = data
        self.created_at = time.time()
        self.size_bytes = len(str(data))
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"backup_id": self.backup_id, "name": self.name,
                "created_at": self.created_at, "size_bytes": self.size_bytes}


class BackupManager:
    def __init__(self) -> None:
        self._backups: Dict[str, BackupEntry] = {}

    def create_backup(self, name: str, data: Dict[str, Any]) -> BackupEntry:
        entry = BackupEntry(name, copy.deepcopy(data))
        self._backups[entry.backup_id] = entry
        return entry

    def restore(self, backup_id: str) -> Optional[Dict[str, Any]]:
        entry = self._backups.get(backup_id)
        return copy.deepcopy(entry.data) if entry else None

    def delete_backup(self, backup_id: str) -> bool:
        if backup_id in self._backups:
            del self._backups[backup_id]
            return True
        return False

    def list_backups(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self._backups.values()]

    def count(self) -> int:
        return len(self._backups)
