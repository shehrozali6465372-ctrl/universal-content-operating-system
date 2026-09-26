"""Bounded dashboard data backend."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class DashboardPanel:
    __slots__ = ("panel_id", "title", "panel_type", "data", "refresh_seconds", "metadata")

    def __init__(self, panel_id: str, title: str, panel_type: str = "graph") -> None:
        if not panel_id.strip() or not title.strip():
            raise ValueError("panel_id and title are required")
        self.panel_id = panel_id
        self.title = title
        self.panel_type = panel_type
        self.data: Any = None
        self.refresh_seconds = 30.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "type": self.panel_type,
            "refresh_seconds": self.refresh_seconds,
        }


class DashboardBackend:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._panels: Dict[str, DashboardPanel] = {}
        self._snapshots: List[Dict[str, Any]] = []

    def add_panel(self, panel_id: str, title: str, panel_type: str = "graph") -> DashboardPanel:
        panel = DashboardPanel(panel_id, title, panel_type)
        with self._lock:
            self._panels[panel_id] = panel
        return panel

    def update_panel_data(self, panel_id: str, data: Any) -> bool:
        with self._lock:
            panel = self._panels.get(panel_id)
            if panel is None:
                return False
            panel.data = data
            return True

    def get_panel(self, panel_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            panel = self._panels.get(panel_id)
            if panel is None:
                return None
            result = panel.to_dict()
            result["data"] = panel.data
            return result

    def list_panels(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [panel.to_dict() for panel in self._panels.values()]

    def get_dashboard(self) -> Dict[str, Any]:
        with self._lock:
            panels = []
            for panel in self._panels.values():
                data = panel.to_dict()
                data["data"] = panel.data
                panels.append(data)
            return {
                "panels": panels,
                "panel_count": len(panels),
                "timestamp": time.time(),
            }

    def snapshot(self) -> Dict[str, Any]:
        snapshot = self.get_dashboard()
        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._history_size:
                del self._snapshots[:-self._history_size]
        return snapshot

    def get_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            return list(self._snapshots[-limit:])

    def remove_panel(self, panel_id: str) -> bool:
        with self._lock:
            return self._panels.pop(panel_id, None) is not None
