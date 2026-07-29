"""MetaManager — Generate SEO titles, meta descriptions, canonical URLs, robots meta."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import MetaGenerationError


class MetaManager:
    """Generate and manage HTML meta tags — title, description, canonical, robots."""

    def __init__(self) -> None:
        self._generation_log: List[dict] = []

    def generate_meta(self, title: str, primary_keyword: str = "",
                       description: str = "", site_name: str = "AI Blog",
                       canonical_url: str = "") -> Dict[str, Any]:
        """Generate complete meta tag set."""
        if not title:
            raise MetaGenerationError("Title is required for meta generation")

        # SEO title (max 60 chars)
        seo_title = title[:60]
        if primary_keyword and primary_keyword.lower() not in seo_title.lower():
            seo_title = f"{primary_keyword.title()}: {seo_title}"
            seo_title = seo_title[:60]

        # Meta description (max 160 chars)
        meta_desc = description[:160] if description else f"Discover {title.lower()}. Expert tips and inspiration."
        if not meta_desc:
            meta_desc = f"Read our guide about {title.lower()}."

        result = {
            "seo_title": seo_title,
            "meta_description": meta_desc[:160],
            "canonical_url": canonical_url or f"https://{site_name.lower().replace(' ', '')}.com/{title.lower().replace(' ', '-')[:30]}",
            "robots_meta": "index, follow",
        }

        self._generation_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_generated": len(self._generation_log)}
