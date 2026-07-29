"""RichPinManager — Article/Product rich pin metadata generation and validation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import RichPinError


class RichPinManager:
    """Manage rich pins — article, product, recipe metadata for Pinterest."""

    RICH_PIN_TYPES = ["article", "product", "recipe", "app"]

    def __init__(self) -> None:
        self._rich_log: List[dict] = []

    def create_article_rich_pin(self, pin, title: str = "", description: str = "",
                                  author: str = "", site_name: str = "",
                                  url: str = "", date_published: str = "") -> Dict[str, Any]:
        """Create article rich pin metadata."""
        metadata = {
            "@type": "Article",
            "headline": title or pin.pin_title,
            "description": description or pin.pin_description[:200],
            "author": author or "Admin",
            "publisher": site_name or "Website",
            "url": url or pin.website_url,
            "datePublished": date_published or "",
        }

        pin.rich_pin_data = metadata
        pin.rich_pin_type = "article"
        pin.is_rich_pin = True

        self._rich_log.append({"pin_id": pin.pin_id, "type": "article"})
        return metadata

    def create_product_rich_pin(self, pin, product_name: str = "",
                                  price: str = "", currency: str = "USD",
                                  availability: str = "in_stock",
                                  brand: str = "") -> Dict[str, Any]:
        """Create product rich pin metadata."""
        metadata = {
            "@type": "Product",
            "name": product_name or pin.pin_title,
            "price": price,
            "currency": currency,
            "availability": availability,
            "brand": brand or "Store",
            "url": pin.website_url or "",
        }

        pin.rich_pin_data = metadata
        pin.rich_pin_type = "product"
        pin.is_rich_pin = True

        self._rich_log.append({"pin_id": pin.pin_id, "type": "product"})
        return metadata

    def validate_rich_pin(self, pin) -> Dict[str, Any]:
        """Validate rich pin metadata completeness."""
        issues: List[str] = []

        if not pin.rich_pin_data:
            issues.append("No rich pin data set")

        if not pin.rich_pin_type:
            issues.append("No rich pin type set")

        if not pin.website_url:
            issues.append("Rich pin requires a website URL")

        if pin.rich_pin_type == "article":
            if not pin.rich_pin_data.get("headline"):
                issues.append("Article rich pin missing headline")
            if not pin.rich_pin_data.get("author"):
                issues.append("Article rich pin missing author")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "type": pin.rich_pin_type,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {"total_rich_pins": len(self._rich_log), "by_type": self.RICH_PIN_TYPES}
