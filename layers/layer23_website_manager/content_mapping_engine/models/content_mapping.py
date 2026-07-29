"""ContentMapping — Core data model for mapping content to website, Pinterest, and affiliates."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class ContentCategory(str, Enum):
    HOME_DECOR = "home_decor"
    FASHION = "fashion"
    BEAUTY = "beauty"
    FOOD = "food"
    TECH = "tech"
    FITNESS = "fitness"
    TRAVEL = "travel"
    FINANCE = "finance"
    DIY = "diy"
    OTHER = "other"


class ContentIntent(str, Enum):
    INFORMATIONAL = "informational"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"
    COMMERCIAL = "commercial"
    ENTERTAINMENT = "entertainment"


class PinStrategy(str, Enum):
    STANDARD = "standard"
    IDEA_PIN = "idea_pin"
    CAROUSEL = "carousel"
    PRODUCT_PIN = "product_pin"
    RICH_PIN = "rich_pin"
    VIDEO = "video"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MappingStatus(str, Enum):
    PENDING = "pending"
    MAPPED = "mapped"
    VALIDATED = "validated"
    FAILED = "failed"
    OVERRIDDEN = "overridden"


@dataclass
class ContentMapping:
    """Complete mapping of content to website, Pinterest, affiliate, and publishing strategy."""

    mapping_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    article_id: str = ""
    article_title: str = ""
    article_content: str = ""

    # Classification
    niche: str = ""
    category: ContentCategory = ContentCategory.OTHER
    intent: ContentIntent = ContentIntent.INFORMATIONAL
    audience: str = ""
    content_type: str = "article"
    confidence: float = 0.0

    # Website mapping
    website_id: str = ""
    website_url: str = ""
    website_category: str = ""
    website_subcategory: str = ""

    # Pinterest mapping
    account_id: str = ""
    account_name: str = ""
    board_id: str = ""
    board_name: str = ""

    # Pin strategy
    pin_strategy: PinStrategy = PinStrategy.STANDARD
    pin_type_reason: str = ""

    # Affiliate mapping
    affiliate_product: str = ""
    affiliate_url: str = ""
    affiliate_program: str = ""
    affiliate_commission: float = 0.0

    # SEO mapping
    seo_keywords: List[str] = field(default_factory=list)
    long_tail_keywords: List[str] = field(default_factory=list)
    search_intent: str = ""
    related_topics: List[str] = field(default_factory=list)

    # Image mapping
    featured_image: str = ""
    pin_image: str = ""
    thumbnail: str = ""
    image_style: str = ""

    # Scheduling
    priority: Priority = Priority.MEDIUM
    suggested_publish_time: float = 0.0
    schedule_reason: str = ""

    # Validation
    validation_score: float = 0.0
    validation_issues: List[str] = field(default_factory=list)
    is_validated: bool = False

    # Status
    status: MappingStatus = MappingStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    mapped_by: str = "ai"

    @property
    def is_mapped(self) -> bool:
        return bool(self.status in (MappingStatus.MAPPED, MappingStatus.VALIDATED))

    @property
    def is_ready(self) -> bool:
        return bool(self.is_validated and self.account_id and self.board_id and self.website_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "article_id": self.article_id,
            "article_title": self.article_title[:80],
            "niche": self.niche,
            "category": self.category.value,
            "intent": self.intent.value,
            "confidence": round(self.confidence, 2),
            "website_id": self.website_id,
            "account_id": self.account_id,
            "board_id": self.board_id,
            "pin_strategy": self.pin_strategy.value,
            "affiliate_product": self.affiliate_product[:50] if self.affiliate_product else "",
            "priority": self.priority.value,
            "validation_score": round(self.validation_score, 1),
            "is_validated": self.is_validated,
            "status": self.status.value,
            "created_at": self.created_at,
        }
