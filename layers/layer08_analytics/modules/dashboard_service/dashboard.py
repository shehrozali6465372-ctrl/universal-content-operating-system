"""Dashboard state service with bounded, collision-safe snapshots."""
from __future__ import annotations
import time
import uuid
from threading import RLock
from typing import Any, Dict, List, Optional


class DashboardWidget:
    __slots__ = ("widget_id", "widget_type", "title", "data_source", "config", "refresh_interval_seconds", "last_updated")
    def __init__(self, widget_id: str = "", widget_type: str = "metric") -> None:
        if not widget_id.strip(): raise ValueError("widget_id is required")
        self.widget_id, self.widget_type = widget_id, widget_type
        self.title = ""; self.data_source = ""; self.config: Dict[str, Any] = {}
        self.refresh_interval_seconds = 300; self.last_updated = 0.0
    def is_stale(self) -> bool:
        return time.time() - self.last_updated > max(0, self.refresh_interval_seconds)
    def to_dict(self) -> Dict[str, Any]:
        return {"widget_id": self.widget_id, "widget_type": self.widget_type, "title": self.title,
                "data_source": self.data_source, "is_stale": self.is_stale()}


class DashboardLayout:
    __slots__ = ("layout_id", "name", "columns", "rows", "widgets")
    def __init__(self, layout_id: str = "", name: str = "") -> None:
        if not layout_id.strip(): raise ValueError("layout_id is required")
        self.layout_id, self.name = layout_id, name; self.columns, self.rows = 4, 3; self.widgets: List[DashboardWidget] = []
    def add_widget(self, widget: DashboardWidget) -> None:
        if self.get_widget(widget.widget_id): raise ValueError("duplicate widget_id")
        self.widgets.append(widget)
    def get_widget(self, widget_id: str) -> Optional[DashboardWidget]:
        return next((w for w in self.widgets if w.widget_id == widget_id), None)
    def to_dict(self) -> Dict[str, Any]:
        return {"layout_id": self.layout_id, "name": self.name, "columns": self.columns, "rows": self.rows, "widget_count": len(self.widgets)}


class DashboardSnapshot:
    __slots__ = ("snapshot_id", "layout_id", "widgets_data", "timestamp")
    def __init__(self, layout_id: str = "") -> None:
        self.snapshot_id, self.layout_id, self.timestamp = f"snap_{uuid.uuid4().hex}", layout_id, time.time()
        self.widgets_data: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"snapshot_id": self.snapshot_id, "layout_id": self.layout_id, "widget_count": len(self.widgets_data), "timestamp": self.timestamp}


class DashboardService:
    def __init__(self) -> None:
        self._layouts: Dict[str, DashboardLayout] = {}; self._snapshots: List[DashboardSnapshot] = []
        self._serving_count = 0; self._lock = RLock()
    def create_layout(self, layout_id: str, name: str) -> DashboardLayout:
        with self._lock:
            if layout_id in self._layouts: raise ValueError(f"layout already exists: {layout_id}")
            layout = DashboardLayout(layout_id, name); self._layouts[layout_id] = layout; return layout
    def add_widget(self, layout_id: str, widget: DashboardWidget) -> bool:
        with self._lock:
            layout = self._layouts.get(layout_id)
            if not layout: return False
            layout.add_widget(widget); return True
    def get_layout(self, layout_id: str) -> Optional[DashboardLayout]:
        with self._lock: return self._layouts.get(layout_id)
    def get_all_layouts(self) -> List[DashboardLayout]:
        with self._lock: return list(self._layouts.values())
    def take_snapshot(self, layout_id: str, data: Dict[str, Any]) -> Optional[DashboardSnapshot]:
        if not isinstance(data, dict): raise ValueError("snapshot data must be a mapping")
        with self._lock:
            if layout_id not in self._layouts: return None
            snapshot = DashboardSnapshot(layout_id); snapshot.widgets_data = dict(data)
            self._snapshots.append(snapshot); self._serving_count += 1; return snapshot
    def get_latest_snapshot(self, layout_id: str) -> Optional[DashboardSnapshot]:
        with self._lock:
            for snapshot in reversed(self._snapshots):
                if snapshot.layout_id == layout_id: return snapshot
        return None
    def get_snapshots(self, layout_id: str = "", limit: int = 10) -> List[DashboardSnapshot]:
        if limit < 0: raise ValueError("limit must be non-negative")
        with self._lock:
            result = [s for s in self._snapshots if not layout_id or s.layout_id == layout_id]
            return list(result[-limit:]) if limit else []
    @property
    def serving_count(self) -> int:
        with self._lock: return self._serving_count
