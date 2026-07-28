"""SEOMetadata — Search engine optimization data model."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SEOMetadata:
    """Full SEO metadata for a page or article."""

    meta_title: str = ""
    meta_description: str = ""
    focus_keyword: str = ""
    keywords: List[str] = field(default_factory=list)

    # Open Graph
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = "article"
    og_url: str = ""

    # Twitter Card
    twitter_card: str = "summary_large_image"
    twitter_title: str = ""
    twitter_description: str = ""
    twitter_image: str = ""

    # Structured Data
    schema_type: str = "Article"
    schema_data: Dict[str, Any] = field(default_factory=dict)

    # Technical
    canonical_url: str = ""
    is_indexable: bool = True
    nofollow_links: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "focus_keyword": self.focus_keyword,
            "keywords": self.keywords,
            "og_title": self.og_title,
            "og_description": self.og_description,
            "og_image": self.og_image,
            "og_type": self.og_type,
            "og_url": self.og_url,
            "twitter_card": self.twitter_card,
            "twitter_title": self.twitter_title,
            "twitter_description": self.twitter_description,
            "twitter_image": self.twitter_image,
            "schema_type": self.schema_type,
            "canonical_url": self.canonical_url,
            "is_indexable": self.is_indexable,
        }

    @classmethod
    def from_article(cls, article_title: str, article_excerpt: str = "",
                     focus_keyword: str = "", site_name: str = "") -> "SEOMetadata":
        """Generate SEO metadata from article content."""
        title = article_title[:60] if len(article_title) > 60 else article_title
        if site_name:
            title = f"{article_title[:55]} — {site_name}"

        desc = article_excerpt or article_title
        desc = desc[:160] if len(desc) > 160 else desc

        return cls(
            meta_title=title,
            meta_description=desc,
            focus_keyword=focus_keyword,
            og_title=article_title[:95],
            og_description=desc,
            twitter_title=article_title[:70],
            twitter_description=desc,
        )
