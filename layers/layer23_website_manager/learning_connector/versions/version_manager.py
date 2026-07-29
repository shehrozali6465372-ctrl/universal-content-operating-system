"""VersionManager — Maintain learning and strategy version history."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import StrategyVersion


class VersionManager:
    """Manage strategy versions with rollback support."""

    def __init__(self) -> None:
        self._versions: List[StrategyVersion] = []
        self._lock = threading.RLock()
        self._current_version: str = "1.0.0"
        self._version_counter: int = 1

    def create_version(self, changes: str = "",
                       performance_score: float = 0.0,
                       config_snapshot: Optional[Dict] = None) -> StrategyVersion:
        with self._lock:
            self._version_counter += 1
            version_str = f"1.{self._version_counter}.0"
            sv = StrategyVersion(version_str, changes, performance_score,
                                 config_snapshot)
            self._versions.append(sv)
            self._current_version = version_str
        return sv

    def get_current_version(self) -> str:
        return self._current_version

    def get_version(self, version: str) -> Optional[StrategyVersion]:
        for v in self._versions:
            if v.version == version:
                return v
        return None

    def get_all_versions(self) -> List[StrategyVersion]:
        return list(self._versions)

    def rollback(self, version: str) -> Optional[Dict[str, Any]]:
        target = self.get_version(version)
        if not target or not target.rollback_available:
            return None
        with self._lock:
            self._current_version = version
            return dict(target.config_snapshot)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_versions": len(self._versions),
                "current_version": self._current_version,
                "rollback_available": any(v.rollback_available for v in self._versions),
            }
