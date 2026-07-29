"""ProductMatcher — AI-powered matching between content and affiliate products."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.exceptions import ProductMatchingError


class ProductMatcher:
    """Match articles/content to the best affiliate products by niche, keywords, and intent."""

    def __init__(self) -> None:
        self._match_log: List[dict] = []

    def match_product(self, niche: str, title: str = "", content: str = "",
                       keywords: Optional[List[str]] = None,
                       available_products: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Find the best matching product for given content."""
        if not available_products:
            return {"product_id": "", "product_name": "", "confidence": 0.0, "reason": "No products available"}

        best_product = None
        best_score = 0
        match_reason = ""

        # Build search text from title, content, keywords
        search_text = (title + " " + content + " " + " ".join(keywords or [])).lower()

        for product in available_products:
            score = 0.0

            # Match by niche (strong signal)
            if hasattr(product, 'niche') and product.niche == niche:
                score += 30

            # Match by keywords
            if hasattr(product, 'keywords') and product.keywords:
                for kw in product.keywords:
                    if kw.lower() in search_text:
                        score += 10

            # Match by product name
            if hasattr(product, 'product_name') and product.product_name:
                name_words = product.product_name.lower().split()
                for w in name_words:
                    if w in search_text and len(w) > 3:
                        score += 8

            # Bonus for high rating
            if hasattr(product, 'rating') and product.rating >= 4.5:
                score += 5

            # Bonus for high commission
            if hasattr(product, 'commission_rate') and product.commission_rate >= 8:
                score += 5

            if score > best_score:
                best_score = score
                best_product = product
                match_reason = f"Matched by niche ({niche}) and content keywords"

        if best_product is None:
            return {"product_id": "", "product_name": "", "confidence": 0.0, "reason": "No matching product found"}

        confidence = min(best_score / 100.0, 1.0)

        result = {
            "product": best_product,
            "product_id": best_product.product_id if hasattr(best_product, 'product_id') else "",
            "product_name": best_product.product_name if hasattr(best_product, 'product_name') else "",
            "confidence": round(confidence, 2),
            "score": best_score,
            "reason": match_reason,
        }

        self._match_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_matches": len(self._match_log)}
