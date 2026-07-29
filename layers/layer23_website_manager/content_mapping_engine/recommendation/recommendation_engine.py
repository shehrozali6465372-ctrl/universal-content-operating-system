"""RecommendationEngine — Smart recommendations to improve content mapping."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import RecommendationError


class RecommendationEngine:
    """Analyze mapping and recommend improvements across all dimensions."""

    def __init__(self) -> None:
        self._recommendation_log: List[dict] = []
        self._total_recommendations = 0

    def recommend(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Generate smart recommendations to improve the mapping."""
        recommendations: List[Dict[str, Any]] = []

        # Website recommendations
        if not mapping.get("website_id"):
            recommendations.append({
                "type": "website",
                "priority": "high",
                "message": "Assign content to a website for publishing",
                "action": "Select website by niche",
            })
        elif not mapping.get("website_category"):
            recommendations.append({
                "type": "website",
                "priority": "medium",
                "message": "Assign website category for better SEO",
                "action": "Auto-detect category from content",
            })

        # Pinterest recommendations
        if not mapping.get("account_id"):
            recommendations.append({
                "type": "pinterest",
                "priority": "high",
                "message": "Assign to a Pinterest account",
                "action": "Select account by niche",
            })
        elif not mapping.get("board_id"):
            recommendations.append({
                "type": "pinterest",
                "priority": "high",
                "message": "Select a board within the account",
                "action": "Map to best matching board",
            })

        # Pin strategy
        if not mapping.get("pin_strategy") or mapping.get("pin_strategy") == "standard":
            recommendations.append({
                "type": "pin",
                "priority": "medium",
                "message": "Consider using Rich Pin or Idea Pin for better engagement",
                "action": "Upgrade pin strategy based on content type",
            })

        # Affiliate recommendations
        if not mapping.get("affiliate_product"):
            recommendations.append({
                "type": "affiliate",
                "priority": "medium",
                "message": "Add an affiliate product to monetize this content",
                "action": "Auto-select product by niche",
            })

        # SEO recommendations
        keywords = mapping.get("seo_keywords", [])
        if len(keywords) < 3:
            recommendations.append({
                "type": "seo",
                "priority": "high",
                "message": f"Only {len(keywords)} keywords - add more for better discovery",
                "action": "Generate keyword list from title and content",
            })

        # Image recommendations
        if not mapping.get("featured_image"):
            recommendations.append({
                "type": "image",
                "priority": "medium",
                "message": "Add featured image for visual appeal",
                "action": "Auto-select image by niche and content type",
            })

        # Scheduling
        priority = mapping.get("priority", "medium")
        if priority == "low":
            recommendations.append({
                "type": "scheduling",
                "priority": "low",
                "message": "Low priority content - consider if this should be published",
                "action": "Review content quality and intent",
            })

        result = {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "high_priority": sum(1 for r in recommendations if r["priority"] == "high"),
            "overall_quality_score": self._calculate_quality(mapping, recommendations),
        }

        self._recommendation_log.append(result)
        self._total_recommendations += 1
        return result

    def _calculate_quality(self, mapping: Dict[str, Any],
                            recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall mapping quality score (0-100)."""
        score = 100.0
        for rec in recommendations:
            if rec["priority"] == "high":
                score -= 15
            elif rec["priority"] == "medium":
                score -= 8
            elif rec["priority"] == "low":
                score -= 3
        return max(0, score)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_recommendations": self._total_recommendations}
