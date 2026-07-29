"""SEOOptimizer — Improve low SEO scores, weak keywords, missing rich data, etc."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.models.seo_models import SEOProfile


class SEOOptimizer:
    """Analyze and suggest improvements for SEO profiles."""

    TITLE_IMPROVEMENTS = [
        "Add primary keyword at start of title",
        "Keep title under 60 characters",
        "Use power words (Ultimate, Best, Essential)",
        "Include year for freshness",
        "Add pipe separator for branding",
    ]
    DESC_IMPROVEMENTS = [
        "Include primary keyword in first 50 chars",
        "Add call-to-action",
        "Include USP (unique selling point)",
        "Keep under 160 characters",
        "Match search intent",
    ]

    def __init__(self) -> None:
        self._optimization_log: List[dict] = []

    def analyze(self, profile: SEOProfile) -> Dict[str, Any]:
        """Analyze SEO profile and suggest improvements."""
        suggestions: List[str] = []
        priority = "low"

        if profile.seo_score >= 80:
            suggestions.append("Profile is well optimized")
            priority = "low"
        elif profile.seo_score >= 60:
            suggestions.append("Profile needs moderate optimization")
            if not profile.primary_keyword:
                suggestions.append(f"Add primary keyword. {random.choice(self.TITLE_IMPROVEMENTS)}")
            if not profile.has_schema:
                suggestions.append("Add schema markup for rich results")
            priority = "medium"
        else:
            suggestions.append("Profile needs significant optimization")
            suggestions.append(f"Optimize title: {random.choice(self.TITLE_IMPROVEMENTS)}")
            suggestions.append(f"Optimize description: {random.choice(self.DESC_IMPROVEMENTS)}")
            suggestions.append("Add structured data (Article or Product schema)")
            suggestions.append("Add Open Graph and Twitter Card meta tags")
            priority = "high"

        if not profile.internal_links:
            suggestions.append("Add internal links to related content")
        if not profile.pinterest_hashtags:
            suggestions.append("Add Pinterest hashtags for better discovery")

        result = {
            "profile_id": profile.profile_id,
            "priority": priority,
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
        }

        self._optimization_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyzed": len(self._optimization_log)}
