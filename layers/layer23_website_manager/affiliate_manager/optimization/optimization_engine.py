"""OptimizationEngine — AI-driven optimization: low CTR, low conversion, low revenue products."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import AffiliateProduct


class OptimizationEngine:
    """Analyze affiliate performance and suggest/apply optimizations."""

    OPTIMIZATION_TIPS = [
        "Replace with higher commission product",
        "Improve product description with benefits",
        "Add customer review highlights",
        "Use urgency in call-to-action",
        "Test different anchor text",
        "Move link higher in content",
        "Add comparison with alternatives",
        "Include product image next to link",
        "Test different affiliate network",
        "Add price comparison table",
    ]

    def __init__(self) -> None:
        self._optimization_log: List[dict] = []

    def analyze_product(self, product: AffiliateProduct) -> Dict[str, Any]:
        """Analyze a product's performance and suggest optimizations."""
        suggestions: List[str] = []
        priority = "low"

        if product.total_clicks > 0:
            if product.conversion_rate < 1.0:
                suggestions.append(f"Low conversion rate ({product.conversion_rate}%). {random.choice(self.OPTIMIZATION_TIPS)}")
                priority = "high"
            elif product.conversion_rate < 3.0:
                suggestions.append(f"Below average conversion ({product.conversion_rate}%)")
                priority = "medium"

            if product.epc < 0.05:
                suggestions.append(f"Low EPC (${product.epc}). Consider higher commission product")
                priority = "high"

        if product.rating < 4.0:
            suggestions.append(f"Product rating low ({product.rating}). Consider better-rated alternative")
            priority = "medium"

        if not product.affiliate_link:
            suggestions.append("No affiliate link set")

        if product.commission_rate < 5.0:
            suggestions.append(f"Commission rate low ({product.commission_rate}%). Look for better offers")
            priority = "medium"

        if product.price < 10.0:
            suggestions.append("Low price point. Consider higher-priced alternatives for better commission")

        result = {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "priority": priority,
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
        }

        self._optimization_log.append(result)
        return result

    def batch_analyze(self, products: List[AffiliateProduct]) -> List[Dict[str, Any]]:
        """Analyze multiple products."""
        results = [self.analyze_product(p) for p in products]
        return sorted(results, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["priority"], 3))

    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyzed": len(self._optimization_log)}
