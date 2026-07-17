"""ContentGenerator — Main content generation engine."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_CG_COUNTER = itertools.count(1)

CONTENT_TYPES = ("social_post", "thread", "article", "blog_post", "video_script",
                 "email", "landing_page", "product_description", "reel_script",
                 "carousel", "newsletter", "tutorial", "case_study")


class GeneratedContent:
    """A piece of generated content."""

    __slots__ = ("content_id", "content_type", "platform", "text", "title",
                 "hashtags", "metadata", "quality_score", "created_at",
                 "generation_time_ms")

    def __init__(self, content_type: str = "", platform: str = "") -> None:
        self.content_id: str = f"gc_{next(_CG_COUNTER)}"
        self.content_type = content_type
        self.platform = platform
        self.text: str = ""
        self.title: str = ""
        self.hashtags: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.quality_score: float = 0.0
        self.created_at: float = time.time()
        self.generation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id, "content_type": self.content_type,
            "platform": self.platform, "title": self.title,
            "text_length": len(self.text), "hashtag_count": len(self.hashtags),
            "quality_score": round(self.quality_score, 3),
        }


class ContentGenerator:
    """Generate content for any platform using configurable strategies."""

    PLATFORM_LIMITS = {
        "facebook": {"max_text": 63206, "max_hashtags": 30, "max_images": 10},
        "instagram": {"max_text": 2200, "max_hashtags": 30, "max_images": 10},
        "x": {"max_text": 280, "max_hashtags": 5, "max_images": 4},
        "linkedin": {"max_text": 3000, "max_hashtags": 5, "max_images": 1},
        "youtube": {"max_title": 100, "max_description": 5000, "max_tags": 500},
        "tiktok": {"max_text": 2200, "max_hashtags": 10, "max_images": 0},
        "pinterest": {"max_description": 500, "max_hashtags": 20},
        "threads": {"max_text": 500, "max_hashtags": 10},
        "medium": {"max_title": 100, "max_text": 100000},
        "wordpress": {"max_title": 200, "max_text": 100000},
        "reddit": {"max_title": 300, "max_text": 40000},
        "telegram": {"max_text": 4096, "max_images": 10},
        "discord": {"max_text": 2000, "max_images": 10},
        "binance_square": {"max_text": 2000, "max_hashtags": 10},
    }

    def __init__(self) -> None:
        self._generated: List[GeneratedContent] = []
        self._strategies: Dict[str, Any] = {}

    def generate(self, topic: str, platform: str = "facebook",
                 content_type: str = "social_post",
                 context: Optional[Dict[str, Any]] = None) -> GeneratedContent:
        start = time.time()
        content = GeneratedContent(content_type, platform)
        content.title = f"{topic} — {content_type}"
        content.text = self._generate_text(topic, platform, content_type, context)
        content.hashtags = self._generate_hashtags(topic, platform)
        content.metadata = {"topic": topic, "context": context or {}}
        content.generation_time_ms = (time.time() - start) * 1000
        self._generated.append(content)
        return content

    def generate_batch(self, topics: List[str], platform: str = "facebook",
                       content_type: str = "social_post") -> List[GeneratedContent]:
        return [self.generate(t, platform, content_type) for t in topics]

    def get_limits(self, platform: str) -> Dict[str, Any]:
        return self.PLATFORM_LIMITS.get(platform, {"max_text": 1000})

    def _generate_text(self, topic: str, platform: str, content_type: str,
                        context: Optional[Dict[str, Any]] = None) -> str:
        limits = self.get_limits(platform)
        max_len = limits.get("max_text", 1000)
        text = f"{topic}. " * 5
        if content_type == "article":
            text = f"Article about {topic}. " * 20
        elif content_type == "thread":
            text = f"Thread on {topic}. " * 10
        return text[:max_len]

    def _generate_hashtags(self, topic: str, platform: str) -> List[str]:
        limits = self.get_limits(platform)
        max_tags = limits.get("max_hashtags", 5)
        words = topic.lower().split()
        tags = [f"#{w}" for w in words if len(w) > 2]
        return tags[:max_tags]

    def get_generated(self, limit: int = 10) -> List[GeneratedContent]:
        return list(self._generated[-limit:])

    def get_stats(self) -> Dict[str, Any]:
        return {"total_generated": len(self._generated),
                "platforms": list(set(c.platform for c in self._generated))}
