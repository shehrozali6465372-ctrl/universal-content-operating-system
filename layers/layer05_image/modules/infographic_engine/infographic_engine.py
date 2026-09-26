"""Infographic Engine — Plan data visualization images."""
from __future__ import annotations

import uuid
from threading import RLock
from typing import Any, Dict, List, Optional


CHART_TYPES = ["bar", "line", "pie", "progress", "comparison", "timeline", "flowchart"]
PLATFORM_DIMENSIONS = {
    "pinterest": (1000, 1500),
    "instagram": (1080, 1350),
    "linkedin": (1200, 1200),
}


class InfographicPlan:
    """Plan for an infographic."""

    __slots__ = ("plan_id", "topic", "chart_type", "data_points",
                 "title", "subtitle", "dimensions", "color_scheme")

    def __init__(self, topic: str = "") -> None:
        self.plan_id = f"info_{uuid.uuid4().hex}"
        self.topic = topic
        self.chart_type = "bar"
        self.data_points: List[Dict[str, Any]] = []
        self.title = ""
        self.subtitle = ""
        self.dimensions = (1080, 1350)
        self.color_scheme = "modern"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "topic": self.topic,
            "chart_type": self.chart_type,
            "data_points": self.data_points,
            "title": self.title,
            "dimensions": {"width": self.dimensions[0], "height": self.dimensions[1]},
        }


class InfographicEngine:
    """Plans infographic data visualizations."""

    def __init__(self) -> None:
        self._plan_count = 0
        self._counter_lock = RLock()

    def plan(self, topic: str, data: Optional[List[Dict[str, Any]]] = None,
             chart_type: str = "bar", platform: str = "pinterest") -> InfographicPlan:
        """Plan an infographic."""
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must not be empty")
        if chart_type not in CHART_TYPES:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        if data is not None and not isinstance(data, list):
            raise ValueError("data must be a list or None")
        if platform not in PLATFORM_DIMENSIONS:
            raise ValueError(f"Unsupported infographic platform: {platform}")

        ip = InfographicPlan(topic=topic.strip())
        ip.chart_type = chart_type
        ip.title = topic.strip()
        ip.data_points = [dict(point) for point in (data or [])]
        ip.dimensions = PLATFORM_DIMENSIONS[platform]
        with self._counter_lock:
            self._plan_count += 1
        return ip

    def suggest_chart(self, data_type: str = "comparison") -> str:
        """Suggest chart type based on data."""
        suggestions = {
            "comparison": "bar", "trend": "line", "proportion": "pie",
            "progress": "progress", "process": "flowchart", "sequence": "timeline",
        }
        return suggestions.get(data_type, "bar")

    @property
    def plan_count(self) -> int:
        with self._counter_lock:
            return self._plan_count
