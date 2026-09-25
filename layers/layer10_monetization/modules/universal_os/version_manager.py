"""VersionManager — unique version registry with explicit rollback history."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class VersionEntry:
    def __init__(self, version: str, description: str = "") -> None:
        self.version_id = f"ver_{version}"
        self.version = version
        self.description = description
        self.components: Dict[str, str] = {}
        self.created_at = time.time()
        self.is_current = False


class VersionManager:
    def __init__(self, current_version: str = "1.0.0") -> None:
        if not current_version:
            raise ValueError("current_version is required")
        self._versions: List[VersionEntry] = []
        self._current_version = current_version
        entry = VersionEntry(current_version, "Initial version")
        entry.is_current = True
        self._versions.append(entry)

    def register_version(self, version: str, description: str = "",
                         components: Optional[Dict[str, str]] = None) -> VersionEntry:
        if not version:
            raise ValueError("version is required")
        existing = next((entry for entry in self._versions if entry.version == version), None)
        if existing is not None:
            return existing
        entry = VersionEntry(version, description)
        entry.components = dict(components or {})
        self._versions.append(entry)
        return entry

    def set_current(self, version: str) -> bool:
        entry = next((item for item in self._versions if item.version == version), None)
        if entry is None:
            return False
        for item in self._versions:
            item.is_current = item is entry
        self._current_version = version
        return True

    def rollback(self) -> Optional[str]:
        current_index = next(
            (index for index, entry in enumerate(self._versions) if entry.is_current), None
        )
        if current_index is None or current_index == 0:
            return None
        previous = self._versions[current_index - 1]
        return previous.version if self.set_current(previous.version) else None

    def get_current(self) -> str:
        return self._current_version

    def get_all(self) -> List[VersionEntry]:
        return list(self._versions)

    def get_previous(self) -> Optional[str]:
        current_index = next(
            (index for index, entry in enumerate(self._versions) if entry.is_current), None
        )
        return self._versions[current_index - 1].version if current_index and current_index > 0 else None

    def get_stats(self) -> Dict[str, Any]:
        return {"current": self._current_version, "total_versions": len(self._versions)}
