"""Memory Archive — Archive and retrieve old memory entries."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_MA_COUNTER = itertools.count(1)


class ArchiveEntry:
    """An archived memory entry."""

    __slots__ = ("archive_id", "original_id", "data", "archived_at",
                 "reason", "tags", "can_restore")

    def __init__(self, original_id: str = "", data: Optional[Dict] = None) -> None:
        self.archive_id: str = f"arc_{next(_MA_COUNTER)}"
        self.original_id = original_id
        self.data: Dict[str, Any] = data or {}
        self.archived_at: float = time.time()
        self.reason: str = ""
        self.tags: List[str] = []
        self.can_restore: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archive_id": self.archive_id,
            "original_id": self.original_id,
            "archived_at": self.archived_at,
            "reason": self.reason,
            "can_restore": self.can_restore,
        }


class MemoryArchive:
    """Archive, search, and restore old memory entries."""

    def __init__(self, max_archives: int = 50000) -> None:
        self._max_archives = max_archives
        self._entries: List[ArchiveEntry] = []

    def archive(self, original_id: str, data: Dict[str, Any],
                reason: str = "", tags: Optional[List[str]] = None) -> ArchiveEntry:
        entry = ArchiveEntry(original_id, data)
        entry.reason = reason
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_archives:
            self._entries = self._entries[-self._max_archives:]
        return entry

    def search(self, original_id: str = "", reason: str = "",
               tag: str = "", limit: int = 50) -> List[ArchiveEntry]:
        results = list(self._entries)
        if original_id:
            results = [e for e in results if e.original_id == original_id]
        if reason:
            results = [e for e in results if e.reason == reason]
        if tag:
            results = [e for e in results if tag in e.tags]
        return results[-limit:]

    def get_by_archive_id(self, archive_id: str) -> Optional[ArchiveEntry]:
        for e in self._entries:
            if e.archive_id == archive_id:
                return e
        return None

    def restore(self, archive_id: str) -> Optional[Dict[str, Any]]:
        entry = self.get_by_archive_id(archive_id)
        if entry and entry.can_restore:
            return dict(entry.data)
        return None

    def get_recent(self, count: int = 10) -> List[ArchiveEntry]:
        return list(self._entries[-count:])

    def get_stats(self) -> Dict[str, Any]:
        restoreable = sum(1 for e in self._entries if e.can_restore)
        return {
            "total_archived": len(self._entries),
            "restoreable": restoreable,
            "non_restoreable": len(self._entries) - restoreable,
        }

    @property
    def archive_count(self) -> int:
        return len(self._entries)
