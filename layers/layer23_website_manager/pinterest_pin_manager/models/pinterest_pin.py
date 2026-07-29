"""PinterestPin — Core data model for a Pinterest Pin with full publishing metadata."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class PinStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class PinType(str, Enum):
    ARTICLE = "article"
    PRODUCT = "product"
    IDEA = "idea"
    VIDEO = "video"
    RICH = "rich"


@dataclass
class PinterestPin:
    """Complete Pinterest Pin with AI-generated content, SEO, and publishing metadata."""

    pin_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    account_id: str = ""
    board_id: str = ""
    article_id: str = ""

    # Content
    pin_title: str = ""
    pin_description: str = ""
    alt_text: str = ""
    call_to_action: str = ""
    pin_type: PinType = PinType.ARTICLE
    content_source: str = ""

    # Images
    image_path: str = ""
    image_url: str = ""
    image_alt: str = ""
    image_width: int = 1000  # Pinterest recommends 1000x1500
    image_height: int = 1500
    image_quality: float = 0.0
    multiple_images: List[str] = field(default_factory=list)

    # SEO
    seo_title: str = ""
    seo_description: str = ""
    seo_keywords: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    search_intent: str = ""
    seo_score: float = 0.0

    # Links
    website_url: str = ""
    affiliate_url: str = ""
    link_title: str = ""
    link_description: str = ""

    # Rich Pin metadata
    rich_pin_type: str = ""  # article, product, recipe, etc.
    rich_pin_data: Dict[str, Any] = field(default_factory=dict)
    is_rich_pin: bool = False

    # Publishing
    status: PinStatus = PinStatus.DRAFT
    publish_time: float = 0.0
    published_at: float = 0.0
    scheduler_job_id: str = ""
    retry_count: int = 0
    max_retries: int = 3
    last_error: str = ""
    is_ai_generated: bool = False

    # Metadata
    niche: str = ""
    note: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Performance (cached)
    total_impressions: int = 0
    total_saves: int = 0
    total_clicks: int = 0
    total_outbound_clicks: int = 0
    ctr: float = 0.0

    @property
    def display_title(self) -> str:
        return self.seo_title or self.pin_title

    @property
    def is_published(self) -> bool:
        return self.status == PinStatus.PUBLISHED

    @property
    def is_failed(self) -> bool:
        return self.status == PinStatus.FAILED

    @property
    def can_retry(self) -> bool:
        return self.is_failed and self.retry_count < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pin_id": self.pin_id,
            "account_id": self.account_id,
            "board_id": self.board_id,
            "article_id": self.article_id,
            "pin_title": self.pin_title,
            "pin_description": self.pin_description[:100] if self.pin_description else "",
            "alt_text": self.alt_text,
            "call_to_action": self.call_to_action,
            "image_path": self.image_path,
            "seo_score": round(self.seo_score, 1),
            "keywords": self.seo_keywords[:8],
            "hashtags": self.hashtags[:8],
            "website_url": self.website_url,
            "is_rich_pin": self.is_rich_pin,
            "status": self.status.value,
            "is_ai_generated": self.is_ai_generated,
            "publish_time": self.publish_time,
            "retry_count": self.retry_count,
            "last_error": self.last_error[:100] if self.last_error else "",
            "impressions": self.total_impressions,
            "saves": self.total_saves,
            "clicks": self.total_clicks,
            "ctr": round(self.ctr, 2),
            "created_at": self.created_at,
        }

    @classmethod
    def from_article(cls, article_title: str, article_content: str,
                     article_id: str = "", website_url: str = "") -> "PinterestPin":
        """Create a pin draft from an article."""
        return cls(
            article_id=article_id,
            pin_title=article_title[:100],
            pin_description=article_content[:500] if article_content else "",
            website_url=website_url,
            content_source=article_content,
            is_ai_generated=True,
        )
