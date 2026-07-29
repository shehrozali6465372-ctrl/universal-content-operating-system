"""SEO data models — profiles, analytics, scores, content types."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class ContentType(str, Enum):
    ARTICLE = "article"
    BLOG_POSTING = "blog_posting"
    PRODUCT = "product"
    RECIPE = "recipe"
    VIDEO = "video"
    WEBSITE = "website"


@dataclass
class SEOProfile:
    """Complete SEO profile for an article/pin with metadata, schema, and rich data."""

    profile_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    article_id: str = ""
    article_title: str = ""

    # Keywords
    primary_keyword: str = ""
    secondary_keywords: List[str] = field(default_factory=list)
    long_tail_keywords: List[str] = field(default_factory=list)
    lsi_keywords: List[str] = field(default_factory=list)
    search_intent: str = "informational"

    # Meta
    seo_title: str = ""
    meta_description: str = ""
    canonical_url: str = ""
    robots_meta: str = "index, follow"

    # Pinterest SEO
    pin_seo_title: str = ""
    pin_description: str = ""
    pinterest_keywords: List[str] = field(default_factory=list)
    pinterest_hashtags: List[str] = field(default_factory=list)

    # Rich Pins
    rich_pin_type: str = ""  # article, product
    rich_pin_data: Dict[str, Any] = field(default_factory=dict)
    is_rich_pin: bool = False

    # Open Graph
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_url: str = ""
    og_type: str = "article"

    # Twitter Card
    twitter_title: str = ""
    twitter_description: str = ""
    twitter_image: str = ""
    twitter_card_type: str = "summary_large_image"

    # Schema
    schema_type: ContentType = ContentType.ARTICLE
    schema_data: Dict[str, Any] = field(default_factory=dict)
    has_schema: bool = False

    # Internal SEO
    internal_links: List[str] = field(default_factory=list)
    anchor_texts: List[str] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)
    topic_cluster: str = ""

    # Scoring
    seo_score: float = 0.0
    readability_score: float = 0.0

    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def is_optimized(self) -> bool:
        return self.seo_score >= 70

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "article_title": self.article_title[:60],
            "primary_keyword": self.primary_keyword,
            "keyword_count": len(self.secondary_keywords) + 1,
            "seo_title": self.seo_title[:60] if self.seo_title else "",
            "meta_description": self.meta_description[:80] if self.meta_description else "",
            "seo_score": round(self.seo_score, 1),
            "is_optimized": self.is_optimized,
            "has_schema": self.has_schema,
            "is_rich_pin": self.is_rich_pin,
            "pinterest_hashtags": len(self.pinterest_hashtags),
            "internal_links": len(self.internal_links),
        }


@dataclass
class SEOAnalytics:
    """Track SEO performance — impressions, clicks, CTR, rankings."""

    analytics_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    article_id: str = ""
    date: float = field(default_factory=time.time)

    google_impressions: int = 0
    google_clicks: int = 0
    google_ctr: float = 0.0
    google_avg_position: float = 0.0

    pinterest_impressions: int = 0
    pinterest_clicks: int = 0
    pinterest_saves: int = 0

    is_indexed: bool = False
    seo_score: float = 0.0

    @property
    def total_traffic(self) -> int:
        return self.google_clicks + self.pinterest_clicks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "google_impressions": self.google_impressions,
            "google_clicks": self.google_clicks,
            "google_ctr": round(self.google_ctr, 2),
            "pinterest_impressions": self.pinterest_impressions,
            "pinterest_clicks": self.pinterest_clicks,
            "is_indexed": self.is_indexed,
            "total_traffic": self.total_traffic,
        }


@dataclass
class SEOScore:
    """Granular SEO scoring breakdown."""
    total: float = 0.0
    keyword_score: float = 0.0
    meta_score: float = 0.0
    pinterest_score: float = 0.0
    schema_score: float = 0.0
    readability_score: float = 0.0
    internal_links_score: float = 0.0
    def to_dict(self) -> Dict[str, float]:
        return {k: round(v, 1) for k, v in self.__dict__.items()}
