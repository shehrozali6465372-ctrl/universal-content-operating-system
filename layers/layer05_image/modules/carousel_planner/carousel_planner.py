"""Carousel Planner — Plan multi-slide carousel content."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class CarouselSlide:
    """A single carousel slide."""
    __slots__ = ("slide_number", "title", "content", "image_prompt",
                 "layout", "is_cover", "is_cta")

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
        self.plan_id = f"carousel_{int(time.time() * 1000) % 10000000}"
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
            "slides": [s.to_dict() for s in self.slides],
        }


class CarouselPlanner:
    """Plans carousel content for social platforms."""

    def __init__(self) -> None:
        self._plan_count = 0

    def plan(self, topic: str, platform: str = "instagram",
             key_points: Optional[List[str]] = None,
             slide_count: int = 5) -> CarouselPlan:
        """Plan a carousel with slides."""
        cp = CarouselPlan(topic=topic, platform=platform)
        points = key_points or [f"Point {i+1} about {topic}" for i in range(slide_count - 2)]

        # Cover slide
        cover = CarouselSlide(1)
        cover.title = topic
        cover.is_cover = True
        cover.layout = "centered"
        cp.slides.append(cover)

        # Content slides
        for i, point in enumerate(points[:slide_count - 2]):
            slide = CarouselSlide(i + 2)
            slide.title = f"Point {i + 1}"
            slide.content = point
            slide.layout = "overlay"
            cp.slides.append(slide)

        # CTA slide
        cta = CarouselSlide(len(cp.slides) + 1)
        cta.title = "Follow for more!"
        cta.is_cta = True
        cp.slides.append(cta)

        cp.total_slides = len(cp.slides)
        self._plan_count += 1
        return cp

    @property
    def plan_count(self) -> int:
        return self._plan_count
