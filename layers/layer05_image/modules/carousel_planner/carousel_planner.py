"""Carousel Planner — Plan multi-slide carousel content."""
from __future__ import annotations

import uuid
from threading import RLock
from typing import Any, Dict, List, Optional

SUPPORTED_CAROUSEL_PLATFORMS = {
    "facebook", "instagram", "linkedin", "pinterest", "threads"
}


class CarouselSlide:
    """A single carousel slide."""

    __slots__ = (
        "slide_number", "title", "content", "image_prompt",
        "layout", "is_cover", "is_cta"
    )

    def __init__(self, slide_number: int = 1) -> None:
        self.slide_number = slide_number
        self.title = ""
        self.content = ""
        self.image_prompt = ""
        self.layout = "centered"
        self.is_cover = False
        self.is_cta = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_number": self.slide_number,
            "title": self.title,
            "content": self.content,
            "is_cover": self.is_cover,
            "is_cta": self.is_cta,
        }


class CarouselPlan:
    """A plan for a carousel post."""

    __slots__ = ("plan_id", "topic", "platform", "slides", "total_slides")

    def __init__(self, topic: str = "", platform: str = "instagram") -> None:
        self.plan_id = f"carousel_{uuid.uuid4().hex}"
        self.topic = topic
        self.platform = platform
        self.slides: List[CarouselSlide] = []
        self.total_slides = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "topic": self.topic,
            "platform": self.platform,
            "total_slides": self.total_slides,
            "slides": [slide.to_dict() for slide in self.slides],
        }


class CarouselPlanner:
    """Plans carousel content for social platforms."""

    def __init__(self) -> None:
        self._plan_count = 0
        self._counter_lock = RLock()

    def plan(
        self,
        topic: str,
        platform: str = "instagram",
        key_points: Optional[List[str]] = None,
        slide_count: int = 5,
    ) -> CarouselPlan:
        """Plan a carousel with exactly slide_count slides."""
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must not be empty")
        if platform not in SUPPORTED_CAROUSEL_PLATFORMS:
            raise ValueError(f"Unsupported carousel platform: {platform}")
        if not isinstance(slide_count, int) or isinstance(slide_count, bool):
            raise ValueError("slide_count must be an integer")
        if slide_count < 3 or slide_count > 20:
            raise ValueError("slide_count must be between 3 and 20")
        if key_points is not None and not isinstance(key_points, list):
            raise ValueError("key_points must be a list")
        if key_points is not None and len(key_points) != slide_count - 2:
            raise ValueError(
                "key_points must contain exactly slide_count - 2 items"
            )
        if key_points is not None and any(
            not isinstance(point, str) or not point.strip() for point in key_points
        ):
            raise ValueError("key_points must contain non-empty strings")

        cp = CarouselPlan(topic=topic.strip(), platform=platform)
        points = key_points or [
            f"Point {index + 1} about {topic.strip()}"
            for index in range(slide_count - 2)
        ]

        cover = CarouselSlide(1)
        cover.title = topic.strip()
        cover.is_cover = True
        cp.slides.append(cover)

        for index, point in enumerate(points):
            slide = CarouselSlide(index + 2)
            slide.title = f"Point {index + 1}"
            slide.content = point
            slide.layout = "overlay"
            cp.slides.append(slide)

        cta = CarouselSlide(slide_count)
        cta.title = "Follow for more!"
        cta.is_cta = True
        cp.slides.append(cta)
        cp.total_slides = slide_count

        with self._counter_lock:
            self._plan_count += 1
        return cp

    @property
    def plan_count(self) -> int:
        with self._counter_lock:
            return self._plan_count
