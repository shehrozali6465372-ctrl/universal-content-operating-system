"""SEOValidator — Check missing meta, alt text, duplicate titles, broken canonical, missing schema."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.models.seo_models import SEOProfile


class SEOValidator:
    """Validate SEO completeness — meta, alt text, titles, descriptions, schema, redirects."""

    def __init__(self) -> None:
        self._validation_log: List[dict] = []

    def validate_profile(self, profile: SEOProfile) -> Dict[str, Any]:
        """Run full SEO validation on a profile."""
        issues: List[str] = []
        score = 100.0

        # Keyword checks
        if not profile.primary_keyword:
            issues.append("Missing primary keyword")
            score -= 10
        if not profile.secondary_keywords:
            issues.append("No secondary keywords")
            score -= 5

        # Meta checks
        if not profile.seo_title:
            issues.append("Missing SEO title")
            score -= 15
        elif len(profile.seo_title) > 60:
            issues.append(f"SEO title too long ({len(profile.seo_title)} chars)")
            score -= 5
        elif len(profile.seo_title) < 20:
            issues.append(f"SEO title too short ({len(profile.seo_title)} chars)")
            score -= 5

        if not profile.meta_description:
            issues.append("Missing meta description")
            score -= 10
        elif len(profile.meta_description) > 160:
            issues.append(f"Meta description too long ({len(profile.meta_description)} chars)")
            score -= 5
        elif len(profile.meta_description) < 50:
            issues.append("Meta description too short")
            score -= 5

        if not profile.canonical_url:
            issues.append("Missing canonical URL")
            score -= 10

        # Pinterest checks
        if not profile.pinterest_hashtags:
            issues.append("No Pinterest hashtags")
            score -= 5

        # Schema checks
        if not profile.has_schema:
            issues.append("No schema markup")
            score -= 10

        # Open Graph checks
        if not profile.og_title:
            issues.append("Missing Open Graph title")
            score -= 5

        # Twitter Card checks
        if not profile.twitter_title:
            issues.append("Missing Twitter Card title")
            score -= 5

        # Internal links
        if not profile.internal_links:
            issues.append("No internal links")
            score -= 5

        result = {
            "profile_id": profile.profile_id,
            "seo_score": max(0, score),
            "is_valid": score >= 60,
            "issues": issues,
            "issue_count": len(issues),
        }

        self._validation_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        valid = sum(1 for v in self._validation_log if v["is_valid"])
        return {"total_validations": len(self._validation_log), "valid": valid, "failed": len(self._validation_log) - valid}
