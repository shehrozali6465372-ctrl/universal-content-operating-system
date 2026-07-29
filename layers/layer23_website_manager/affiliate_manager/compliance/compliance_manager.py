"""ComplianceManager — Check FTC disclosure, affiliate disclosure, Pinterest/website rules."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.exceptions import ComplianceError


class ComplianceManager:
    """Ensure affiliate content complies with FTC, Pinterest, and website regulations."""

    DISCLOSURE_TEMPLATES = {
        "ftc": "This post contains affiliate links. We may earn a commission if you make a purchase.",
        "pinterest": "Affiliate Link: This pin contains affiliate links. As an Amazon Associate we earn from qualifying purchases.",
        "website": "Disclosure: Some of the links in this article are affiliate links. We may earn a small commission at no extra cost to you.",
    }

    def __init__(self) -> None:
        self._compliance_log: List[dict] = []

    def check_disclosure(self, content: str, platform: str = "website") -> Dict[str, Any]:
        """Check if content contains proper disclosure."""
        issues: List[str] = []
        content_lower = content.lower()

        disclosure_keywords = ["affiliate", "commission", "disclosure", "sponsored", "paid"]
        found = [kw for kw in disclosure_keywords if kw in content_lower]

        if not found:
            issues.append(f"No affiliate disclosure found for {platform}")

        if "affiliate" not in content_lower:
            issues.append("Missing 'affiliate' keyword in disclosure")

        result = {
            "platform": platform,
            "has_disclosure": len(issues) == 0,
            "disclosure_keywords_found": found,
            "issues": issues,
            "recommended_disclosure": self.DISCLOSURE_TEMPLATES.get(platform, self.DISCLOSURE_TEMPLATES["website"]),
        }

        self._compliance_log.append(result)
        return result

    def generate_disclosure(self, platform: str = "website") -> str:
        """Generate a compliant disclosure statement."""
        return self.DISCLOSURE_TEMPLATES.get(platform, self.DISCLOSURE_TEMPLATES["website"])

    def check_pinterest_compliance(self, pin_description: str) -> Dict[str, Any]:
        """Check Pinterest-specific compliance rules."""
        issues = []
        desc_lower = pin_description.lower()

        if "affiliate" in desc_lower or "commission" in desc_lower:
            if len(pin_description) < 50:
                issues.append("Pin description too short for affiliate disclosure")

        if any(w in desc_lower for w in ["buy now", "shop now", "click here"]):
            issues.append("Pinterest may restrict promotional language")

        result = {
            "is_compliant": len(issues) == 0,
            "issues": issues,
        }

        self._compliance_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_checks": len(self._compliance_log)}
