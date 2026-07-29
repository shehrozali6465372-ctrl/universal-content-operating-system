"""OpenGraphManager — Generate og:title, og:description, og:image, og:url, og:type."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import OpenGraphError


class OpenGraphManager:
    """Generate Open Graph meta tags for social sharing."""

    def __init__(self) -> None:
        self._og_log: List[dict] = []

    def generate_og_tags(self, title: str, description: str = "",
                           image_url: str = "", url: str = "",
                           og_type: str = "article",
                           site_name: str = "AI Blog") -> Dict[str, Any]:
        """Generate complete Open Graph tags."""
        if not title:
            raise OpenGraphError("Title required for Open Graph")

        result = {
            "og:title": title[:60],
            "og:description": description[:200] if description else title[:200],
            "og:image": image_url or "https://default-image.com/og.png",
            "og:url": url or "",
            "og:type": og_type,
            "og:site_name": site_name,
        }

        self._og_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_og_tags": len(self._og_log)}
