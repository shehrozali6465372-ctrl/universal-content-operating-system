"""BackupManager — integrity-checked in-memory snapshots."""
from __future__ import annotations
import copy
import hashlib
import json
import time
import itertools
from typing import Any, Dict, List, Optional

_BM_COUNTER = itertools.count(1)


class BackupEntry:
    def __init__(self, backup_type: str, description: str) -> None:
        self.backup_id = f"bak_{next(_BM_COUNTER)}"
        self.backup_type = backup_type
        self.description = description
        self.data: Dict[str, Any] = {}
        self.checksum = ""
        self.size_bytes = 0
        self.created_at = time.time()
        self.status = "completed"


class BackupManager:
    """Create and restore immutable process-local snapshots.

    This manager is intentionally in-memory; durable backup requires the persistence layer.
    """

    def __init__(self) -> None:
        self._backups: List[BackupEntry] = []

    def create(self, backup_type: str, data: Dict[str, Any],
               description: str = "") -> BackupEntry:
        if not backup_type:
            raise ValueError("backup_type is required")
        snapshot = copy.deepcopy(data)
        encoded = json.dumps(snapshot, sort_keys=True, default=str).encode()
        entry = BackupEntry(backup_type, description)
        entry.data = snapshot
        entry.checksum = hashlib.sha256(encoded).hexdigest()
        entry.size_bytes = len(encoded)
        self._backups.append(entry)
        return entry

    def restore(self, backup_id: str) -> Optional[Dict[str, Any]]:
        for backup in self._backups:
            if backup.backup_id != backup_id:
                continue
            encoded = json.dumps(backup.data, sort_keys=True, default=str).encode()
            if hashlib.sha256(encoded).hexdigest() != backup.checksum:
                backup.status = "corrupt"
                return None
            return copy.deepcopy(backup.data)
        return None

    def delete(self, backup_id: str) -> bool:
        for index, backup in enumerate(self._backups):
            if backup.backup_id == backup_id:
                self._backups.pop(index)
                return True
        return False

    def get_recent(self, count: int = 5) -> List[BackupEntry]:
        return list(self._backups[-max(0, count):])

    def get_by_type(self, backup_type: str) -> List[BackupEntry]:
        return [backup for backup in self._backups if backup.backup_type == backup_type]

    def get_total_size(self) -> int:
        return sum(backup.size_bytes for backup in self._backups)

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for backup in self._backups:
            types[backup.backup_type] = types.get(backup.backup_type, 0) + 1
        return {"total_backups": len(self._backups), "total_size_bytes": self.get_total_size(),
                "by_type": types}
