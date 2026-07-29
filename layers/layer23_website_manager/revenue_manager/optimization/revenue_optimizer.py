"""RevenueOptimizer — Recommend better merchants, products, commissions, strategies."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RevenueOptimizer:
    RECOMMENDATIONS = [
        "Focus on high-commission products (ClickBank, Digistore24 offer 40-50%)",
        "Improve content-to-product matching for better conversion",
        "Test different affiliate networks for same product category",
        "Add price comparison tables to increase click-through",
        "Use urgency in CTAs (Limited Time, Only X Left)",
        "Optimize for high-intent keywords (buy, best, review)",
        "Cross-promote products between related articles",
        "Focus on top 20% products generating 80% of revenue",
    ]

    def __init__(self):
        self._log: List[Dict] = []

    def analyze(self, product_summary: Dict, merchant_summary: Dict,
                 total_revenue: float, total_cost: float) -> Dict[str, Any]:
        suggestions = []
        if total_revenue > 0:
            margin = ((total_revenue - total_cost) / total_revenue) * 100
            if margin < 20: suggestions.append("Profit margin below 20%. Reduce costs or increase prices.")
            elif margin > 70: suggestions.append("Healthy profit margin. Consider scaling ad spend.")
        if product_summary.get("total_products", 0) < 5:
            suggestions.append("Only a few products. Diversify affiliate product portfolio.")
        suggestions.extend(self.RECOMMENDATIONS[:3])
        result = {"suggestions": suggestions, "count": len(suggestions)}
        self._log.append(result)
        return result

    def get_stats(self) -> Dict: return {"total_analyses": len(self._log)}
