"""Image Planner — Plans what images to create (independent of writing)."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


PLATFORM_IMAGE_SPECS = {
    "facebook": {"feed": (1200, 630), "story": (1080, 1920), "cover": (820, 312), "carousel": (1080, 1080)},
    "instagram": {"feed": (1080, 1080), "story": (1080, 1920), "reel_cover": (1080, 1920), "carousel": (1080, 1080)},
    "twitter": {"tweet": (1200, 675), "header": (1500, 500)},
    "linkedin": {"feed": (1200, 627), "article": (1200, 644), "banner": (1584, 396)},
    "tiktok": {"video_cover": (1080, 1920), "thumbnail": (1080, 1920)},
    "youtube": {"thumbnail": (1280, 720), "banner": (2560, 1440), "end_screen": (1280, 720)},
    "pinterest": {"pin": (1000, 1500), "story": (1080, 1920)},
    "threads": {"post": (1080, 1080), "story": (1080, 1920)},
}

IMAGE_TYPES = {
    "photo": "Realistic photo-style image",
    "illustration": "Hand-drawn or digital illustration",
    "infographic": "Data visualization with text",
    "carousel": "Multi-slide image set",
    "thumbnail": "Eye-catching preview image",
    "meme": "Humorous image with text overlay",
    "quote": "Text overlay on background",
    "before_after": "Split comparison image",
    "diagram": "Flowchart or process diagram",
    "product": "Product showcase image",
}


class ImagePlan:
    """A plan for a single image."""
    __slots__ = ("plan_id", "image_type", "description", "platform", "dimensions",
                 "style", "text_overlay", "color_scheme", "priority", "metadata")

    def __init__(self, image_type: str = "photo", platform: str = "facebook") -> None:
        self.plan_id = f"imgplan_{int(time.time() * 1000) % 10000000}"
        self.image_type = image_type
        self.description = ""
        self.platform = platform
        self.dimensions = PLATFORM_IMAGE_SPECS.get(platform, {}).get("feed", (1080, 1080))
        self.style = "modern"
        self.text_overlay = ""
        self.color_scheme = ""
        self.priority = "medium"
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "image_type": self.image_type,
            "description": self.description,
            "platform": self.platform,
            "dimensions": {"width": self.dimensions[0], "height": self.dimensions[1]},
            "style": self.style,
            "text_overlay": self.text_overlay,
            "priority": self.priority,
        }


class ImagePlanner:
    """Plans images for content (independent of writing pipeline)."""

    def __init__(self) -> None:
        self._plan_count = 0

    def plan(self, topic: str, platform: str = "facebook",
             image_type: str = "photo", count: int = 1) -> List[ImagePlan]:
        """Create image plans for a topic."""
        plans: List[ImagePlan] = []
        for _ in range(count):
            ip = ImagePlan(image_type=image_type, platform=platform)
            ip.description = f"{image_type} image about {topic}"
            ip.dimensions = PLATFORM_IMAGE_SPECS.get(platform, {}).get("feed", (1080, 1080))
            plans.append(ip)
        self._plan_count += len(plans)
        return plans

    def plan_multi_platform(self, topic: str, platforms: Optional[List[str]] = None,
                             image_type: str = "photo") -> Dict[str, List[ImagePlan]]:
        """Plan images for multiple platforms."""
        plats = platforms or ["facebook", "instagram", "twitter", "linkedin"]
        result: Dict[str, List[ImagePlan]] = {}
        for p in plats:
            result[p] = self.plan(topic, p, image_type)
        return result

    def suggest_type(self, goal: str = "educate", platform: str = "facebook") -> str:
        """Suggest image type based on goal and platform."""
        if goal == "educate":
            return "infographic" if platform in ("pinterest", "linkedin") else "illustration"
        if goal == "entertain":
            return "meme" if platform in ("facebook", "instagram") else "photo"
        if goal == "promote":
            return "product" if platform == "instagram" else "photo"
        if goal == "inspire":
            return "quote" if platform in ("instagram", "pinterest") else "photo"
        return "photo"

    @property
    def plan_count(self) -> int:
        return self._plan_count
