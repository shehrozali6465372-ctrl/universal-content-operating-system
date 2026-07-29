"""TwitterCardManager — Generate Twitter Card meta tags."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import TwitterCardError


class TwitterCardManager:
    """Generate Twitter Card meta tags — title, description, image, card type."""

    def __init__(self) -> None:
        self._card_log: List[dict] = []

    def generate_twitter_card(self, title: str, description: str = "",
                                image_url: str = "", card_type: str = "summary_large_image",
                                site: str = "@aisystem") -> Dict[str, Any]:
        """Generate Twitter Card metadata."""
        if not title:
            raise TwitterCardError("Title required for Twitter Card")

        result = {
            "twitter:card": card_type,
            "twitter:title": title[:60],
            "twitter:description": description[:200] if description else title[:200],
            "twitter:image": image_url or "",
            "twitter:site": site,
        }

        self._card_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_cards": len(self._card_log)}
