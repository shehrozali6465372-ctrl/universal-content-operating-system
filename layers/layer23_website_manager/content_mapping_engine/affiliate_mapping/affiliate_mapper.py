"""AffiliateMapper — Automatically detect best affiliate product and link for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.exceptions import AffiliateMappingError


class AffiliateMapper:
    """Map content to the best affiliate product, program, and commission."""

    # Predefined affiliate products by niche
    AFFILIATE_PRODUCTS: Dict[str, List[Dict[str, Any]]] = {
        "home_decor": [
            {"product": "Bed Frame Set", "url": "https://amzn.to/bedframe", "program": "Amazon",
             "commission": 8.0},
            {"product": "LED Strip Lights", "url": "https://amzn.to/ledlights", "program": "Amazon",
             "commission": 5.0},
        ],
        "fashion": [
            {"product": "Casual Blazer", "url": "https://amzn.to/blazer", "program": "Amazon",
             "commission": 7.0},
        ],
        "beauty": [
            {"product": "Vitamin C Serum", "url": "https://amzn.to/vitc", "program": "Amazon",
             "commission": 10.0},
        ],
        "food": [
            {"product": "Air Fryer", "url": "https://amzn.to/airfryer", "program": "Amazon",
             "commission": 6.0},
        ],
        "tech": [
            {"product": "Wireless Earbuds", "url": "https://amzn.to/earbuds", "program": "Amazon",
             "commission": 4.0},
        ],
        "fitness": [
            {"product": "Yoga Mat", "url": "https://amzn.to/yogamat", "program": "Amazon",
             "commission": 5.0},
        ],
        "travel": [
            {"product": "Travel Backpack", "url": "https://amzn.to/backpack", "program": "Amazon",
             "commission": 6.0},
        ],
        "finance": [
            {"product": "Personal Finance Book", "url": "https://amzn.to/financebook", "program": "Amazon",
             "commission": 4.0},
        ],
        "diy": [
            {"product": "Tool Set", "url": "https://amzn.to/toolset", "program": "Amazon",
             "commission": 5.0},
        ],
    }

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []

    def map_affiliate(self, niche: str, topic: str = "") -> Dict[str, Any]:
        """Map content to the best affiliate product."""
        products = self.AFFILIATE_PRODUCTS.get(niche, [])

        if not products:
            return {"product": "", "url": "", "program": "", "commission": 0.0, "confidence": 0.0}

        # Try topic match
        if topic:
            topic_lower = topic.lower()
            for p in products:
                if any(w in p["product"].lower() for w in topic_lower.split()):
                    result = {**p, "confidence": 0.85}
                    self._mapping_log.append(result)
                    return result

        # Default to first product with highest commission
        best = max(products, key=lambda p: p["commission"])
        result = {**best, "confidence": 0.7}
        self._mapping_log.append(result)
        return result

    def get_available_products(self, niche: str) -> List[Dict[str, Any]]:
        return self.AFFILIATE_PRODUCTS.get(niche, [])

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mappings": len(self._mapping_log)}
