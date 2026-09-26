"""Thumbnail Engine — Generate eye-catching thumbnail plans."""
from __future__ import annotations
import uuid
from threading import RLock
from typing import Any, Dict

THUMBNAIL_DIMENSIONS = {
    "youtube": (1280, 720), "facebook": (1200, 630), "twitter": (1200, 675)
}


class ThumbnailPlan:
    """Plan for a thumbnail image."""
    __slots__ = ("plan_id", "topic", "style", "text", "dimensions",
                 "color_scheme", "face_position", "cta_overlay")

    def __init__(self, topic: str = "") -> None:
        self.plan_id = f"thumb_{uuid.uuid4().hex}"
        self.topic = topic
        self.style = "bold"
        self.text = ""
        self.dimensions = (1280, 720)
        self.color_scheme = "contrast"
        self.face_position = "center"
        self.cta_overlay = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id, "topic": self.topic, "style": self.style,
            "text": self.text,
            "dimensions": {"width": self.dimensions[0], "height": self.dimensions[1]},
            "color_scheme": self.color_scheme,
        }


class ThumbnailEngine:
    """Plans thumbnails for videos and posts."""
    def __init__(self) -> None:
        self._plan_count = 0
        self._counter_lock = RLock()

    def plan(self, topic: str, platform: str = "youtube", style: str = "bold") -> ThumbnailPlan:
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must not be empty")
        if platform not in THUMBNAIL_DIMENSIONS:
            raise ValueError(f"Unsupported thumbnail platform: {platform}")
        if not isinstance(style, str) or not style.strip():
            raise ValueError("style must not be empty")
        tp = ThumbnailPlan(topic=topic.strip())
        tp.style = style.strip()
        tp.text = topic.strip()[:40]
        tp.dimensions = THUMBNAIL_DIMENSIONS[platform]
        with self._counter_lock:
            self._plan_count += 1
        return tp

    @property
    def plan_count(self) -> int:
        with self._counter_lock:
            return self._plan_count
