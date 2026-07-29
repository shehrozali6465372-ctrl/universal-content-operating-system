"""RecommendationEngine — Smart recommendations for better mapping alternatives."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentMapping, PinStrategy,
)


class RecommendationEngine:
    """Analyze mappings and recommend better alternatives — board, website, affiliate, keywords, image."""

    def __init__(self) -> None:
        self._recommendation_log: List[dict] = []

    def recommend_improvements(self, mapping: ContentMapping) -> Dict[str, Any]:
        """Analyze mapping and suggest improvements."""
        recommendations: List[str] = []

        # Board recommendations
        if not mapping.board_name:
            recommendations.append(f"Map to a board in {mapping.niche} niche for better reach")

        # Affiliate recommendations
        if not mapping.affiliate_product:
            recommendations.append(f"Add affiliate product for monetization in {mapping.niche}")

        # SEO recommendations
        if not mapping.seo_keywords:
            recommendations.append("Add SEO keywords for better discoverability")
        elif len(mapping.seo_keywords) < 3:
            recommendations.append("Add more SEO keywords (minimum 3)")

        # Pin strategy recommendations
        if mapping.intent and mapping.intent.value in ("educational", "how-to"):
            recommendations.append("Use Idea Pin for step-by-step educational content")

        # Scheduling recommendations
        if mapping.priority and mapping.priority.value == "low":
            recommendations.append("Consider scheduling during peak hours for better engagement")

        # Validation score recommendations
        if mapping.validation_score < 60:
            recommendations.append("Fix validation issues before publishing")

        result = {
            "mapping_id": mapping.mapping_id,
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
        }

        self._recommendation_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_recommendations": len(self._recommendation_log)}
