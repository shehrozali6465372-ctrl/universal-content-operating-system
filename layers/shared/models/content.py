"""
Shared Content Models
Frozen interface — v1.0.0
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class ContentPost:
    """A piece of content ready for publishing."""

    __slots__ = (
        "post_id", "title", "body", "hashtags",
        "topic", "niche", "style", "tone",
        "image_prompt", "image_url",
        "platform", "scheduled_at", "status",
        "metadata", "created_at",
    )

    STATUSES = ("draft", "ready", "scheduled", "published", "failed", "archived")

    def __init__(
        self,
        title: str = "",
        body: str = "",
        hashtags: Optional[List[str]] = None,
        topic: str = "",
        niche: str = "general",
        style: str = "informative",
        tone: str = "professional",
    ):
        self.post_id = f"post_{int(datetime.now(timezone.utc).timestamp())}_{hash(title) % 100000}"
        self.title = title
        self.body = body
        self.hashtags = hashtags or []
        self.topic = topic
        self.niche = niche
        self.style = style
        self.tone = tone
        self.image_prompt = ""
        self.image_url = ""
        self.platform = "facebook"
        self.scheduled_at = ""
        self.status = "draft"
        self.metadata: Dict = {}
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "title": self.title,
            "body": self.body,
            "hashtags": list(self.hashtags),
            "topic": self.topic,
            "niche": self.niche,
            "style": self.style,
            "tone": self.tone,
            "image_prompt": self.image_prompt,
            "image_url": self.image_url,
            "platform": self.platform,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContentPost":
        p = cls(
            title=data.get("title", ""),
            body=data.get("body", ""),
            hashtags=data.get("hashtags", []),
            topic=data.get("topic", ""),
            niche=data.get("niche", "general"),
            style=data.get("style", "informative"),
            tone=data.get("tone", "professional"),
        )
        p.post_id = data.get("post_id", p.post_id)
        p.image_prompt = data.get("image_prompt", "")
        p.image_url = data.get("image_url", "")
        p.platform = data.get("platform", "facebook")
        p.scheduled_at = data.get("scheduled_at", "")
        p.status = data.get("status", "draft")
        p.metadata = data.get("metadata", {})
        p.created_at = data.get("created_at", p.created_at)
        return p

    def word_count(self) -> int:
        return len(self.body.split())

    def __repr__(self) -> str:
        return f"ContentPost(title='{self.title[:50]}', status='{self.status}')"


class ContentVariant:
    """A/B test variant of a content post."""

    __slots__ = ("variant_id", "post", "variant_label", "confidence", "metrics")

    def __init__(self, post: ContentPost, variant_label: str = "A"):
        self.variant_id = f"var_{variant_label}_{post.post_id}"
        self.post = post
        self.variant_label = variant_label
        self.confidence = 0.0
        self.metrics: Dict = {}

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "post": self.post.to_dict(),
            "variant_label": self.variant_label,
            "confidence": self.confidence,
            "metrics": self.metrics,
        }

    def __repr__(self) -> str:
        return f"ContentVariant(label='{self.variant_label}')"
