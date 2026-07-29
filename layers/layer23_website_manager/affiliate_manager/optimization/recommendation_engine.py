"""RecommendationEngine — Recommend better products, higher commissions, trending items."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import AffiliateProduct


class AffiliateRecommendationEngine:
    """AI recommendation engine for better product selection."""

    def __init__(self) -> None:
        self._recommendation_log: List[dict] = []

    def recommend_better_product(self, current: AffiliateProduct,
                                   alternatives: List[AffiliateProduct]) -> Dict[str, Any]:
        """Recommend better product based on rating, commission, and price."""
        if not alternatives:
            return {"recommended": None, "reason": "No alternatives available"}

        scored = []
        for alt in alternatives:
            if alt.product_id == current.product_id:
                continue
            score = alt.rating * 10 + alt.commission_rate + min(alt.price / 10, 20)
            scored.append((score, alt))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return {"recommended": None, "reason": "No better alternatives"}

        best = scored[0][0]
        current_score = current.rating * 10 + current.commission_rate + min(current.price / 10, 20)

        if best <= current_score:
            return {"recommended": None, "reason": "Current product is already optimal"}

        recommended = scored[0][1]
        result = {
            "recommended": recommended.product_name,
            "product_id": recommended.product_id,
            "improvement_score": round(best - current_score, 1),
            "reason": f"Higher rating ({recommended.rating}) and commission ({recommended.commission_rate}%)",
        }

        self._recommendation_log.append(result)
        return result

    def get_top_trending(self, products: List[AffiliateProduct], top_k: int = 5) -> List[AffiliateProduct]:
        """Get top trending products by rating and commission."""
        scored = sorted(products, key=lambda p: p.rating * p.commission_rate, reverse=True)
        return scored[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_recommendations": len(self._recommendation_log)}
