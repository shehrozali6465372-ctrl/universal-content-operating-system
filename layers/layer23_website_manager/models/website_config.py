"""WebsiteConfig — Domain configuration model."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class WebsiteConfig:
    """Complete website configuration."""

    # Identity
    site_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    domain: str = "example.com"
    site_name: str = "My Website"
    tagline: str = "A great website powered by AI"

    # Branding
    logo_url: str = ""
    favicon_url: str = ""
    brand_color_primary: str = "#1a73e8"
    brand_color_secondary: str = "#34a853"
    theme: str = "default"
    language: str = "en"
    timezone: str = "UTC"

    # Content defaults
    default_author: str = "Admin"
    default_category: str = "Uncategorized"
    posts_per_page: int = 10
    date_format: str = "YYYY-MM-DD"

    # Social
    social_links: Dict[str, str] = field(default_factory=dict)

    # SEO defaults
    meta_title_format: str = "{title} — {site_name}"
    meta_description: str = ""
    og_image: str = ""

    # Technical
    robots_txt: str = "User-agent: *\nAllow: /"
    enable_sitemap: bool = True
    enable_https: bool = True
    www_redirect: bool = False

    # Timestamps
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_id": self.site_id,
            "domain": self.domain,
            "site_name": self.site_name,
            "tagline": self.tagline,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "brand_color_primary": self.brand_color_primary,
            "brand_color_secondary": self.brand_color_secondary,
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "default_author": self.default_author,
            "default_category": self.default_category,
            "posts_per_page": self.posts_per_page,
            "date_format": self.date_format,
            "social_links": self.social_links,
            "meta_title_format": self.meta_title_format,
            "meta_description": self.meta_description,
            "og_image": self.og_image,
            "enable_sitemap": self.enable_sitemap,
            "enable_https": self.enable_https,
            "www_redirect": self.www_redirect,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebsiteConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
