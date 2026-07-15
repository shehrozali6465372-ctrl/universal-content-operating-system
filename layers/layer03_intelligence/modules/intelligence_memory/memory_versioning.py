"""Memory Versioning — Version memory entries for rollback and history."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional


class MemoryVersion:
    """A versioned snapshot of a memory entry."""
    __slots__ = ("version_id", "entry_id", "data", "version_number",
                 "change_summary", "created_at", "parent_version")

    def __init__(self, entry_id: str = "", data: Optional[Dict] = None, version_number: int = 1) -> None:
        self.version_id = f"ver_{next(_VER_COUNTER)}_{version_number}"
        self.entry_id = entry_id
        self.data = data or {}
        self.version_number = version_number
        self.change_summary = ""
        self.created_at = time.time()
        self.parent_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "entry_id": self.entry_id,
            "version_number": self.version_number,
            "change_summary": self.change_summary,
            "created_at": self.created_at,
            "parent_version": self.parent_version,
        }


_VER_COUNTER = itertools.count(1)


class MemoryVersioner:
    """Tracks versions of memory entries for rollback."""

    def __init__(self) -> None:
        self._versions: Dict[str, List[MemoryVersion]] = {}  # entry_id -> versions

    def create_version(self, entry_id: str, data: Dict[str, Any],
                       change_summary: str = "") -> MemoryVersion:
        """Create a new version for an entry."""
        versions = self._versions.get(entry_id, [])
        vnum = len(versions) + 1
        mv = MemoryVersion(entry_id=entry_id, data=data, version_number=vnum)
        mv.change_summary = change_summary
        if versions:
            mv.parent_version = versions[-1].version_id
        versions.append(mv)
        self._versions[entry_id] = versions
        return mv

    def get_latest(self, entry_id: str) -> Optional[MemoryVersion]:
        versions = self._versions.get(entry_id, [])
        return versions[-1] if versions else None

    def get_version(self, entry_id: str, version_number: int) -> Optional[MemoryVersion]:
        versions = self._versions.get(entry_id, [])
        for v in versions:
            if v.version_number == version_number:
                return v
        return None

    def get_history(self, entry_id: str) -> List[MemoryVersion]:
        return list(self._versions.get(entry_id, []))

    def rollback(self, entry_id: str, to_version: int) -> Optional[MemoryVersion]:
        """Rollback to a specific version by creating a copy."""
        target = self.get_version(entry_id, to_version)
        if target is None:
            return None
        return self.create_version(entry_id, target.data,
                                   change_summary=f"Rollback to version {to_version}")

    def version_count(self, entry_id: str) -> int:
        return len(self._versions.get(entry_id, []))

    def total_versions(self) -> int:
        return sum(len(v) for v in self._versions.values())
