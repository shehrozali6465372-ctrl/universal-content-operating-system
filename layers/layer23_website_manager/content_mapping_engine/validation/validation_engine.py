"""ValidationEngine — Verify mapping correctness for website, account, board, affiliate, images."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import ContentMapping


class ValidationEngine:
    """Validate all mappings — website, account, board, affiliate, images, SEO consistency."""

    def __init__(self) -> None:
        self._validation_log: List[dict] = []

    def validate_mapping(self, mapping: ContentMapping) -> Dict[str, Any]:
        """Run full validation on a content mapping."""
        issues: List[str] = []
        score = 100.0

        # Website validation
        if not mapping.website_id:
            issues.append("No website mapped")
            score -= 20
        elif not mapping.website_url:
            issues.append("Website URL missing")
            score -= 10

        # Account validation
        if not mapping.account_id:
            issues.append("No Pinterest account mapped")
            score -= 20
        elif not mapping.account_name:
            issues.append("Account name missing")
            score -= 5

        # Board validation
        if not mapping.board_id:
            issues.append("No board mapped")
            score -= 20
        elif not mapping.board_name:
            issues.append("Board name missing")
            score -= 5

        # Niche consistency
        if mapping.niche and mapping.category and mapping.niche != mapping.category:
            # Not necessarily invalid, but flag for review
            if mapping.niche.replace("_", "") != mapping.category.replace("_", ""):
                issues.append(f"Niche '{mapping.niche}' vs category '{mapping.category}' mismatch")
                score -= 10

        # Affiliate validation
        if mapping.affiliate_url and not mapping.affiliate_url.startswith("https://"):
            issues.append("Affiliate URL not secure")
            score -= 5

        # SEO validation
        if not mapping.seo_keywords:
            issues.append("No SEO keywords generated")
            score -= 10

        # Image validation
        if not mapping.featured_image:
            score -= 5

        # Pin strategy validation
        if not mapping.pin_strategy:
            issues.append("No pin strategy selected")
            score -= 10

        mapping.validation_score = max(0, score)
        mapping.validation_issues = issues
        mapping.is_validated = score >= 60

        result = {
            "mapping_id": mapping.mapping_id,
            "validation_score": mapping.validation_score,
            "is_validated": mapping.is_validated,
            "issues": issues,
            "issue_count": len(issues),
        }

        self._validation_log.append(result)

        if mapping.is_validated:
            mapping.status = "validated"

        return result

    def get_stats(self) -> Dict[str, Any]:
        validated = sum(1 for v in self._validation_log if v["is_validated"])
        return {
            "total_validations": len(self._validation_log),
            "validated": validated,
            "failed": len(self._validation_log) - validated,
        }
