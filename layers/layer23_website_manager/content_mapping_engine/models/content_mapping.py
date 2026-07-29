"""ContentMapping — Core mapping between content and all publishing targets."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class PinStrategy(str, Enum):
    STANDARD = "standard"
    IDEA = "idea"
    CAROUSEL = "carousel"
    PRODUCT = "product"
    RICH = "rich"
    VIDEO = "video"


class ContentIntent(str, Enum):
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    COMMERCIAL = "commercial"
    INFORMATIONAL = "informational"
    ENTERTAINMENT = "entertainment"


class ContentAudience(str, Enum):
    WOMEN = "women"
    MEN = "men"
    ALL = "all"
    PARENTS = "parents"
    PROFESSIONALS = "professionals"
    STUDENTS = "students"
    HOMEOWNERS = "homeowners"


class MappingPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MappingStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class ContentMapping:
    """Complete mapping of article through entire publishing pipeline."""

    mapping_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    article_id: str = ""
    article_title: str = ""
    niche: str = ""
    category: str = ""
    subcategory: str = ""
    topic: str = ""

    # Classification
    intent: ContentIntent = ContentIntent.INFORMATIONAL
    audience: ContentAudience = ContentAudience.ALL
    content_type: str = "article"
    confidence: float = 0.0

    # Website mapping
    website_id: str = ""
    website_url: str = ""
    website_category: str = ""

    # Pinterest mapping
    account_id: str = ""
    account_name: str = ""
    board_id: str = ""
    board_name: str = ""

    # Pin strategy
    pin_strategy: PinStrategy = PinStrategy.STANDARD
    pin_type: str = "article"

    # Affiliate
    affiliate_product_id: str = ""
    affiliate_product_name: str = ""
    affiliate_url: str = ""
    affiliate_commission: float = 0.0

    # SEO
    seo_keywords: List[str] = field(default_factory=list)
    long_tail_keywords: List[str] = field(default_factory=list)
    search_intent: str = ""
    related_topics: List[str] = field(default_factory=list)

    # Image
    featured_image: str = ""
    pinterest_image: str = ""
    thumbnail: str = ""
    image_style: str = ""

    # Publishing
    priority: MappingPriority = MappingPriority.MEDIUM
    schedule_time: float = 0.0
    schedule_reason: str = ""

    # Status
    status: MappingStatus = MappingStatus.PENDING
    validation_score: float = 0.0
    is_validated: bool = False
    error_message: str = ""

    # Relationships
    related_article_ids: List[str] = field(default_factory=list)
    related_pin_ids: List[str] = field(default_factory=list)
    related_board_ids: List[str] = field(default_factory=list)

    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    mapped_by: str = "ai_engine"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "article_id": self.article_id,
            "article_title": self.article_title[:80] if self.article_title else "",
            "niche": self.niche,
            "category": self.category,
            "intent": self.intent.value,
            "audience": self.audience.value,
            "confidence": round(self.confidence, 2),
            "website_id": self.website_id,
            "account_id": self.account_id,
            "board_id": self.board_id,
            "pin_strategy": self.pin_strategy.value,
            "affiliate_product": self.affiliate_product_name[:50] if self.affiliate_product_name else "",
            "keyword_count": len(self.seo_keywords),
            "priority": self.priority.value,
            "validation_score": round(self.validation_score, 1),
            "is_validated": self.is_validated,
            "status": self.status.value,
            "created_at": self.created_at,
        }

    @property
    def is_active(self) -> bool:
        return self.status == MappingStatus.ACTIVE

    @property
    def is_published(self) -> bool:
        return self.status == MappingStatus.PUBLISHED

    @property
    def is_pending(self) -> bool:
        return self.status == MappingStatus.PENDING
