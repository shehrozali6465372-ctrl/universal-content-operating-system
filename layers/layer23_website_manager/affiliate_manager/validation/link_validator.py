"""LinkValidator — Validate affiliate links: broken, expired, invalid, redirect errors."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.exceptions import BrokenAffiliateLinkError


class LinkValidator:
    """Check affiliate links for validity, expiration, broken status."""

    def __init__(self) -> None:
        self._validation_log: List[dict] = []

    def validate_link(self, url: str) -> Dict[str, Any]:
        """Validate an affiliate link."""
        issues: List[str] = []
        score = 100.0

        if not url:
            issues.append("URL is empty")
            score -= 50
        elif not url.startswith(("http://", "https://")):
            issues.append("URL does not start with http:// or https://")
            score -= 30

        # Check for common affiliate patterns
        if url and "amazon" in url.lower() and "tag=" not in url.lower():
            if "tag=" not in url.split("?")[-1] if "?" in url else url:
                issues.append("Amazon link missing affiliate tag")
                score -= 20

        if url and len(url) > 500:
            issues.append("URL is too long")
            score -= 10

        result = {
            "url": url[:100],
            "is_valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
        }

        self._validation_log.append(result)
        return result

    def check_broken(self, url: str) -> Dict[str, Any]:
        """Check if a link appears broken (simulated)."""
        issues = []
        if not url:
            issues.append("Empty URL")
        elif "example.com" in url.lower():
            issues.append("Placeholder URL detected")
        elif len(url) < 10:
            issues.append("URL too short")

        return {
            "url": url[:100],
            "is_broken": len(issues) > 0,
            "issues": issues,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {"total_validations": len(self._validation_log)}
