"""URLManager — SEO-friendly URL and slug management."""
from __future__ import annotations
import re
import unicodedata
import hashlib
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from layers.layer23_website_manager.exceptions import InvalidSlugError


@dataclass
class Redirect:
    """URL redirect mapping."""
    from_url: str
    to_url: str
    status_code: int = 301  # 301 = permanent, 302 = temporary

    def to_dict(self) -> dict:
        return {"from_url": self.from_url, "to_url": self.to_url, "status_code": self.status_code}


class URLManager:
    """Manages SEO-friendly URLs, slugs, canonical URLs, and redirects."""

    def __init__(self, domain: str = "example.com", use_https: bool = True,
                 www_prefix: bool = False) -> None:
        self._domain = domain
        self._use_https = use_https
        self._www_prefix = www_prefix
        self._existing_slugs: Set[str] = set()
        self._redirects: Dict[str, Redirect] = {}
        self._canonical_urls: Dict[str, str] = {}

    # ─── Slug Generation ───────────────────────────────────

    @staticmethod
    def generate_slug(text: str, max_length: int = 80) -> str:
        """Generate a clean, SEO-friendly URL slug from text."""
        # Normalize unicode
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")

        # Lowercase and clean
        text = text.lower().strip()

        # Remove special chars
        text = re.sub(r"[^a-z0-9\s-]", "", text)

        # Replace spaces with hyphens
        text = re.sub(r"[\s]+", "-", text)

        # Remove consecutive hyphens
        text = re.sub(r"-+", "-", text)

        # Trim hyphens
        text = text.strip("-")

        # Truncate
        if len(text) > max_length:
            text = text[:max_length].rstrip("-")

        return text or "untitled"

    def register_slug(self, slug: str, article_id: str) -> str:
        """Register a slug, making it unique if it already exists."""
        if slug not in self._existing_slugs:
            self._existing_slugs.add(slug)
            return slug

        counter = 1
        while True:
            unique_slug = f"{slug}-{counter}"
            if unique_slug not in self._existing_slugs:
                self._existing_slugs.add(unique_slug)
                return unique_slug
            counter += 1

    def is_slug_available(self, slug: str) -> bool:
        """Check if a slug is available for use."""
        return slug not in self._existing_slugs

    # ─── URL Building ──────────────────────────────────────

    def build_url(self, slug: str) -> str:
        """Build full URL from slug."""
        protocol = "https" if self._use_https else "http"
        domain = f"www.{self._domain}" if self._www_prefix else self._domain
        return f"{protocol}://{domain}/{slug.lstrip('/')}"

    def build_article_url(self, slug: str, category_slug: str = "") -> str:
        """Build article URL with optional category prefix."""
        path = f"{category_slug}/{slug}" if category_slug else slug
        return self.build_url(path)

    def build_canonical_url(self, slug: str) -> str:
        """Generate canonical URL for SEO."""
        url = self.build_url(slug)
        self._canonical_urls[slug] = url
        return url

    def get_canonical_url(self, slug: str) -> Optional[str]:
        """Get stored canonical URL."""
        return self._canonical_urls.get(slug)

    # ─── Redirects ─────────────────────────────────────────

    def add_redirect(self, from_url: str, to_url: str, status_code: int = 301) -> Redirect:
        """Add a URL redirect."""
        redirect = Redirect(from_url=from_url, to_url=to_url, status_code=status_code)
        self._redirects[from_url] = redirect
        return redirect

    def remove_redirect(self, from_url: str) -> bool:
        """Remove a URL redirect."""
        return self._redirects.pop(from_url, None) is not None

    def get_redirect(self, url: str) -> Optional[Redirect]:
        """Get redirect for a URL."""
        return self._redirects.get(url)

    def get_all_redirects(self) -> List[Redirect]:
        """Get all registered redirects."""
        return list(self._redirects.values())

    # ─── Configuration ─────────────────────────────────────

    def configure(self, domain: str = "", use_https: Optional[bool] = None,
                  www_prefix: Optional[bool] = None) -> None:
        """Update URL manager configuration."""
        if domain:
            self._domain = domain
        if use_https is not None:
            self._use_https = use_https
        if www_prefix is not None:
            self._www_prefix = www_prefix

    def to_dict(self) -> dict:
        return {
            "domain": self._domain,
            "use_https": self._use_https,
            "www_prefix": self._www_prefix,
            "existing_slugs": len(self._existing_slugs),
            "redirects": len(self._redirects),
            "canonical_urls": len(self._canonical_urls),
        }
