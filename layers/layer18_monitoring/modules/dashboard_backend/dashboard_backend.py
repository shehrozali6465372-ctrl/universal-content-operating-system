"""DashboardBackend — aggregate monitoring data for dashboard display."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class DashboardPanel:
    __slots__ = ("panel_id", "title", "panel_type", "data", "refresh_seconds",
                 "metadata")

    def __init__(self, panel_id: str, title: str, panel_type: str = "graph") -> None:
        self.panel_id = panel_id
        self.title = title
        self.panel_type = panel_type
        self.data: Any = None
        self.refresh_seconds: float = 30.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"panel_id": self.panel_id, "title": self.title,
                "type": self.panel_type}


class DashboardBackend:
    def __init__(self) -> None:
        self._panels: Dict[str, DashboardPanel] = {}
        self._snapshots: List[Dict[str, Any]] = []

    def add_panel(self, panel_id: str, title: str, panel_type: str = "graph") -> DashboardPanel:
        panel = DashboardPanel(panel_id, title, panel_type)
        self._panels[panel_id] = panel
        return panel

    def update_panel_data(self, panel_id: str, data: Any) -> bool:
        panel = self._panels.get(panel_id)
        if panel:
            panel.data = data
            return True
        return False

    def get_panel(self, panel_id: str) -> Optional[Dict[str, Any]]:
        panel = self._panels.get(panel_id)
        if panel:
            result = panel.to_dict()
            result["data"] = panel.data
            return result
        return None

    def list_panels(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._panels.values()]

    def get_dashboard(self) -> Dict[str, Any]:
        return {"panels": [self.get_panel(pid) for pid in self._panels],
                "panel_count": len(self._panels), "timestamp": time.time()}

    def snapshot(self) -> Dict[str, Any]:
        snap = self.get_dashboard()
        self._snapshots.append(snap)
        return snap

    def get_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._snapshots[-limit:]

    def remove_panel(self, panel_id: str) -> bool:
        if panel_id in self._panels:
            del self._panels[panel_id]
            return True
        return False
