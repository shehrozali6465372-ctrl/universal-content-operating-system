"""backup_history.py — Backup history tracking."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class BackupHistoryEntry:
    """A backup history entry."""
    __slots__ = ("backup_id", "backup_type", "size_bytes", "duration_ms",
                 "status", "timestamp")
    _counter = 0

    def __init__(self, backup_type: str, size_bytes: int, duration_ms: float = 0.0,
                 status: str = "success") -> None:
        BackupHistoryEntry._counter += 1
        self.backup_id: int = BackupHistoryEntry._counter
        self.backup_type = backup_type
        self.size_bytes = size_bytes
        self.duration_ms = duration_ms
        self.status = status
        self.timestamp: float = time.time()


class BackupHistory:
    """Tracks backup history."""

    def __init__(self) -> None:
        self._entries: List[BackupHistoryEntry] = []

    def record(self, backup_type: str, size_bytes: int,
               duration_ms: float = 0.0, status: str = "success") -> BackupHistoryEntry:
        entry = BackupHistoryEntry(backup_type, size_bytes, duration_ms, status)
        self._entries.append(entry)
        return entry

    def get_entries(self, backup_type: str = "", limit: int = 50) -> List[BackupHistoryEntry]:
        entries = self._entries
        if backup_type:
            entries = [e for e in entries if e.backup_type == backup_type]
        return entries[-limit:]

    def total_size(self) -> int:
        return sum(e.size_bytes for e in self._entries)

    def stats(self) -> Dict[str, Any]:
        return {"entries": len(self._entries), "total_size": self.total_size()}
