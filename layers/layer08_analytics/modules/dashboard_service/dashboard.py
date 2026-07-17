"""Dashboard Service — Serve analytics data for dashboards."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class DashboardWidget:
    """A widget on the analytics dashboard."""

    __slots__ = ("widget_id", "widget_type", "title", "data_source",
                 "config", "refresh_interval_seconds", "last_updated")

    def __init__(self, widget_id: str = "", widget_type: str = "metric") -> None:
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.title: str = ""
        self.data_source: str = ""
        self.config: Dict[str, Any] = {}
        self.refresh_interval_seconds: int = 300
        self.last_updated: float = 0.0

    def is_stale(self) -> bool:
        return time.time() - self.last_updated > self.refresh_interval_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "widget_type": self.widget_type,
            "title": self.title,
            "data_source": self.data_source,
            "is_stale": self.is_stale(),
        }


class DashboardLayout:
    """Layout configuration for a dashboard."""

    __slots__ = ("layout_id", "name", "columns", "rows", "widgets")

    def __init__(self, layout_id: str = "", name: str = "") -> None:
        self.layout_id = layout_id
        self.name = name
        self.columns: int = 4
        self.rows: int = 3
        self.widgets: List[DashboardWidget] = []

    def add_widget(self, widget: DashboardWidget) -> None:
        self.widgets.append(widget)

    def get_widget(self, widget_id: str) -> Optional[DashboardWidget]:
        for w in self.widgets:
            if w.widget_id == widget_id:
                return w
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "name": self.name,
            "columns": self.columns,
            "rows": self.rows,
            "widget_count": len(self.widgets),
        }


class DashboardSnapshot:
    """A snapshot of dashboard data at a point in time."""

    __slots__ = ("snapshot_id", "layout_id", "widgets_data", "timestamp")

    def __init__(self, layout_id: str = "") -> None:
        self.snapshot_id: str = f"snap_{int(time.time() * 1000) % 100000}"
        self.layout_id = layout_id
        self.widgets_data: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "layout_id": self.layout_id,
            "widget_count": len(self.widgets_data),
            "timestamp": self.timestamp,
        }


class DashboardService:
    """Serve analytics data for dashboards."""

    def __init__(self) -> None:
        self._layouts: Dict[str, DashboardLayout] = {}
        self._snapshots: List[DashboardSnapshot] = []
        self._serving_count = 0

    def create_layout(self, layout_id: str, name: str) -> DashboardLayout:
        layout = DashboardLayout(layout_id, name)
        self._layouts[layout_id] = layout
        return layout

    def add_widget(self, layout_id: str, widget: DashboardWidget) -> bool:
        layout = self._layouts.get(layout_id)
        if layout:
            layout.add_widget(widget)
            return True
        return False

    def get_layout(self, layout_id: str) -> Optional[DashboardLayout]:
        return self._layouts.get(layout_id)

    def get_all_layouts(self) -> List[DashboardLayout]:
        return list(self._layouts.values())

    def take_snapshot(self, layout_id: str, data: Dict[str, Any]) -> Optional[DashboardSnapshot]:
        layout = self._layouts.get(layout_id)
        if not layout:
            return None
        snapshot = DashboardSnapshot(layout_id)
        snapshot.widgets_data = data
        self._snapshots.append(snapshot)
        self._serving_count += 1
        return snapshot

    def get_latest_snapshot(self, layout_id: str) -> Optional[DashboardSnapshot]:
        for s in reversed(self._snapshots):
            if s.layout_id == layout_id:
                return s
        return None

    def get_snapshots(self, layout_id: str = "", limit: int = 10) -> List[DashboardSnapshot]:
        result = self._snapshots
        if layout_id:
            result = [s for s in result if s.layout_id == layout_id]
        return result[-limit:]

    @property
    def serving_count(self) -> int:
        return self._serving_count
