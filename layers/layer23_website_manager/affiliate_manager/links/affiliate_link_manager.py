"""AffiliateLinkManager — Generate deep links, short links, tracking links, country links."""
from __future__ import annotations
import hashlib
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    AffiliateLink, LinkType,
)
from layers.layer23_website_manager.affiliate_manager.exceptions import LinkGenerationError


class AffiliateLinkManager:
    """Generate, manage, and track affiliate links — deep, short, tracking, country-specific."""

    def __init__(self) -> None:
        self._links: Dict[str, AffiliateLink] = {}
        self._lock = threading.Lock()
        self._total_generated = 0

    def generate_deep_link(self, product_id: str, original_url: str,
                            affiliate_id: str = "") -> AffiliateLink:
        """Generate a deep affiliate link pointing to a specific product."""
        if not original_url.startswith(("http://", "https://")):
            raise LinkGenerationError("Invalid URL")
        if not affiliate_id:
            raise LinkGenerationError("Affiliate ID required")

        affiliate_url = f"{original_url}?tag={affiliate_id}"
        link = AffiliateLink(
            product_id=product_id,
            original_url=original_url,
            affiliate_url=affiliate_url,
            link_type=LinkType.DEEP_LINK,
        )
        with self._lock:
            self._links[link.link_id] = link
            self._total_generated += 1
        return link

    def generate_short_link(self, product_id: str, original_url: str) -> AffiliateLink:
        """Generate a shortened affiliate link."""
        hash_str = hashlib.md5(original_url.encode()).hexdigest()[:8]
        short_url = f"https://go.affiliate/{hash_str}"

        link = AffiliateLink(
            product_id=product_id,
            original_url=original_url,
            short_url=short_url,
            affiliate_url=original_url,
            link_type=LinkType.SHORT_LINK,
        )
        with self._lock:
            self._links[link.link_id] = link
            self._total_generated += 1
        return link

    def generate_tracking_link(self, product_id: str, original_url: str,
                                 source: str = "") -> AffiliateLink:
        """Generate a link with tracking parameters."""
        tracking_params = f"utm_source={source}&utm_medium=affiliate&utm_campaign=universal_ai"
        separator = "?" if "?" not in original_url else "&"
        affiliate_url = f"{original_url}{separator}{tracking_params}"

        link = AffiliateLink(
            product_id=product_id,
            original_url=original_url,
            affiliate_url=affiliate_url,
            link_type=LinkType.TRACKING_LINK,
        )
        with self._lock:
            self._links[link.link_id] = link
            self._total_generated += 1
        return link

    def get_link(self, link_id: str) -> Optional[AffiliateLink]:
        return self._links.get(link_id)

    def get_links_for_product(self, product_id: str) -> List[AffiliateLink]:
        return [l for l in self._links.values() if l.product_id == product_id]

    def deactivate_link(self, link_id: str) -> bool:
        link = self._links.get(link_id)
        if not link:
            return False
        link.is_active = False
        return True

    def record_click(self, link_id: str) -> bool:
        link = self._links.get(link_id)
        if not link:
            return False
        with self._lock:
            link.total_clicks += 1
        return True

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_links": len(self._links),
            "total_generated": self._total_generated,
            "total_clicks": sum(l.total_clicks for l in self._links.values()),
        }
