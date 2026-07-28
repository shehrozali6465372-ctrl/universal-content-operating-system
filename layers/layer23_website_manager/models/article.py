"""Article — Content article model."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ArticleStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    UPDATED = "updated"
    ARCHIVED = "archived"


@dataclass
class Article:
    """A complete website article with content, metadata and SEO."""

    article_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    slug: str = ""
    content: str = ""
    excerpt: str = ""
    category_id: str = ""
    tags: List[str] = field(default_factory=list)
    featured_image: str = ""
    author: str = "Admin"
    status: ArticleStatus = ArticleStatus.DRAFT

    # SEO
    meta_title: str = ""
    meta_description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    canonical_url: str = ""
    is_indexable: bool = True

    # Scheduling
    scheduled_at: float = 0.0
    published_at: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: int = 1

    # Internal linking
    related_article_ids: List[str] = field(default_factory=list)
    internal_links: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "slug": self.slug,
            "content_preview": self.content[:200] if self.content else "",
            "excerpt": self.excerpt,
            "category_id": self.category_id,
            "tags": self.tags,
            "featured_image": self.featured_image,
            "author": self.author,
            "status": self.status.value,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "canonical_url": self.canonical_url,
            "is_indexable": self.is_indexable,
            "scheduled_at": self.scheduled_at,
            "published_at": self.published_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "related_articles": len(self.related_article_ids),
            "internal_links": len(self.internal_links),
        }
