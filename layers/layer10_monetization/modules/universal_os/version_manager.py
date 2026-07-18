"""VersionManager — System versions, plugin versions, rollback support."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class VersionEntry:
    """A version record."""

    __slots__ = ("version_id", "version", "description", "components",
                 "created_at", "is_current")

    def __init__(self, version: str = "", description: str = "") -> None:
        self.version_id: str = f"ver_{version}"
        self.version = version
        self.description = description
        self.components: Dict[str, str] = {}
        self.created_at: float = time.time()
        self.is_current: bool = False


class VersionManager:
    """Manage system versions and support rollback."""

    def __init__(self, current_version: str = "1.0.0") -> None:
        self._versions: List[VersionEntry] = []
        self._current_version = current_version
        entry = VersionEntry(current_version, "Initial version")
        entry.is_current = True
        self._versions.append(entry)

    def register_version(self, version: str, description: str = "",
                         components: Optional[Dict[str, str]] = None) -> VersionEntry:
        entry = VersionEntry(version, description)
        if components:
            entry.components = dict(components)
        self._versions.append(entry)
        return entry

    def set_current(self, version: str) -> bool:
        for v in self._versions:
            if v.version == version:
                for ver in self._versions:
                    ver.is_current = False
                v.is_current = True
                self._current_version = version
                return True
        return False

    def rollback(self) -> Optional[str]:
        if len(self._versions) < 2:
            return None
        for i, v in enumerate(self._versions):
            if v.is_current and i > 0:
                v.is_current = False
                prev = self._versions[i - 1]
                prev.is_current = True
                self._current_version = prev.version
                return prev.version
        return None

    def get_current(self) -> str:
        return self._current_version

    def get_all(self) -> List[VersionEntry]:
        return list(self._versions)

    def get_previous(self) -> Optional[str]:
        for i, v in enumerate(self._versions):
            if v.is_current and i > 0:
                return self._versions[i - 1].version
        return None

    def get_stats(self) -> Dict[str, Any]:
        return {"current": self._current_version, "total_versions": len(self._versions)}
