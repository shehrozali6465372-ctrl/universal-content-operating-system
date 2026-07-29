"""WebsiteLinkManager — Attach website URLs, article links, and affiliate links to pins."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import BrokenWebsiteLinkError


class WebsiteLinkManager:
    """Manage pin-to-website linking: articles, affiliate URLs, link validation."""

    def __init__(self) -> None:
        self._link_log: List[dict] = []

    def attach_article_link(self, pin, article_url: str, article_title: str = "",
                             link_description: str = "") -> bool:
        """Attach an article URL to a pin."""
        if not article_url or not article_url.startswith(("http://", "https://")):
            raise BrokenWebsiteLinkError(f"Invalid URL: {article_url}")

        pin.website_url = article_url
        pin.link_title = article_title or pin.pin_title
        pin.link_description = link_description or pin.pin_description[:200]

        self._link_log.append({
            "pin_id": pin.pin_id,
            "url": article_url,
            "type": "article",
        })
        return True

    def attach_affiliate_link(self, pin, affiliate_url: str,
                               original_url: str = "") -> bool:
        """Attach an affiliate link (overrides or redirects)."""
        pin.affiliate_url = affiliate_url
        if original_url and not pin.website_url:
            pin.website_url = original_url

        self._link_log.append({
            "pin_id": pin.pin_id,
            "url": affiliate_url,
            "type": "affiliate",
        })
        return True

    def validate_link(self, url: str) -> Dict[str, Any]:
        """Validate a website link."""
        is_valid = bool(url and url.startswith(("http://", "https://")))
        return {
            "url": url,
            "is_valid": is_valid,
            "issues": [] if is_valid else ["URL must start with http:// or https://"],
        }

    def get_stats(self) -> Dict[str, Any]:
        return {"total_links": len(self._link_log)}
