"""Thumbnail Engine — Generate eye-catching thumbnail plans."""
from __future__ import annotations
import time
from typing import Any, Dict


class ThumbnailPlan:
    """Plan for a thumbnail image."""
    __slots__ = ("plan_id", "topic", "style", "text", "dimensions",
                 "color_scheme", "face_position", "cta_overlay")

    def __init__(self, topic: str = "") -> None:
        self.plan_id = f"thumb_{int(time.time() * 1000) % 10000000}"
        self.topic = topic
        self.style = "bold"
        self.text = ""
        self.dimensions = (1280, 720)
        self.color_scheme = "contrast"
        self.face_position = "center"
        self.cta_overlay = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "topic": self.topic,
            "style": self.style,
            "text": self.text,
            "dimensions": {"width": self.dimensions[0], "height": self.dimensions[1]},
            "color_scheme": self.color_scheme,
        }


class ThumbnailEngine:
    """Plans thumbnails for videos and posts."""

    def __init__(self) -> None:
        self._plan_count = 0

    def plan(self, topic: str, platform: str = "youtube",
             style: str = "bold") -> ThumbnailPlan:
        """Create a thumbnail plan."""
        tp = ThumbnailPlan(topic=topic)
        tp.style = style
        tp.text = topic[:40]
        dims = {"youtube": (1280, 720), "facebook": (1200, 630), "twitter": (1200, 675)}
        tp.dimensions = dims.get(platform, (1280, 720))
        self._plan_count += 1
        return tp

    @property
    def plan_count(self) -> int:
        return self._plan_count
