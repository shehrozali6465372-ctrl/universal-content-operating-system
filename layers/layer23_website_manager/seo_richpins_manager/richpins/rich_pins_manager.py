"""RichPinsManager — Article and Product Rich Pin metadata generation and validation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import RichPinError


class RichPinsManager:
    """Generate and validate Rich Pin metadata for Pinterest."""

    def __init__(self) -> None:
        self._rich_log: List[dict] = []

    def create_article_rich_pin(self, title: str, description: str = "",
                                  author: str = "AI Blog", site_name: str = "",
                                  url: str = "", date_published: str = "",
                                  image_url: str = "") -> Dict[str, Any]:
        """Generate article rich pin metadata."""
        if not title:
            raise RichPinError("Title required for rich pin")

        metadata = {
            "@type": "Article",
            "headline": title,
            "description": description[:200] if description else "",
            "author": author,
            "publisher": site_name or "AI Blog",
            "url": url,
            "datePublished": date_published,
            "image": image_url,
        }

        result = {
            "rich_pin_type": "article",
            "rich_pin_data": metadata,
            "is_rich_pin": True,
        }

        self._rich_log.append(result)
        return result

    def create_product_rich_pin(self, product_name: str, price: str = "",
                                  currency: str = "USD", availability: str = "in_stock",
                                  brand: str = "", url: str = "",
                                  image_url: str = "") -> Dict[str, Any]:
        """Generate product rich pin metadata."""
        if not product_name:
            raise RichPinError("Product name required for rich pin")

        metadata = {
            "@type": "Product",
            "name": product_name,
            "price": price,
            "currency": currency,
            "availability": availability,
            "brand": brand or "Store",
            "url": url,
            "image": image_url,
        }

        result = {
            "rich_pin_type": "product",
            "rich_pin_data": metadata,
            "is_rich_pin": True,
        }

        self._rich_log.append(result)
        return result

    def validate_rich_pin(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate rich pin metadata completeness."""
        issues = []
        if not metadata.get("headline") and not metadata.get("name"):
            issues.append("Missing headline/name")
        if not metadata.get("url"):
            issues.append("Missing URL")
        if not metadata.get("description"):
            issues.append("Missing description")
        return {"is_valid": len(issues) == 0, "issues": issues}

    def get_stats(self) -> Dict[str, Any]:
        return {"total_rich_pins": len(self._rich_log)}
