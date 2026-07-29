"""PinHealthChecker — Check pin health: broken URLs, missing images, duplicates, missing metadata."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin


class PinHealthChecker:
    """Monitor pin health — broken links, missing images, missing titles, duplicate detection."""

    def __init__(self) -> None:
        self._check_log: List[dict] = []

    def check_pin(self, pin: PinterestPin, all_pins: Optional[List[PinterestPin]] = None) -> Dict[str, Any]:
        """Check health of a single pin."""
        issues: List[str] = []
        score = 100.0

        # Title
        if not pin.pin_title:
            issues.append("Missing pin title")
            score -= 30
        elif len(pin.pin_title) < 5:
            issues.append("Pin title too short")
            score -= 15

        # Description
        if not pin.pin_description:
            issues.append("Missing description")
            score -= 20
        elif len(pin.pin_description) < 30:
            issues.append("Description too short")
            score -= 10

        # Website URL
        if not pin.website_url:
            issues.append("Missing website URL")
            score -= 15
        elif not pin.website_url.startswith(("http://", "https://")):
            issues.append("Invalid website URL")
            score -= 10

        # Image
        if not pin.image_path and not pin.image_url:
            issues.append("Missing image")
            score -= 25

        # Alt text
        if not pin.alt_text:
            issues.append("Missing alt text")
            score -= 5

        # Keywords
        if not pin.seo_keywords:
            issues.append("No SEO keywords")
            score -= 10

        # Duplicate check
        if all_pins:
            for other in all_pins:
                if other.pin_id != pin.pin_id and other.board_id == pin.board_id:
                    if other.pin_title.lower() == pin.pin_title.lower():
                        issues.append(f"Duplicate pin title: '{pin.pin_title}'")
                        score -= 30
                        break

        # SEO score check
        if pin.seo_score < 50:
            issues.append(f"Low SEO score: {pin.seo_score}")
            score -= 10

        result = {
            "pin_id": pin.pin_id,
            "health_score": max(0, score),
            "status": "healthy" if score >= 70 else "degraded" if score >= 40 else "critical",
            "issues": issues,
            "issue_count": len(issues),
            "checked_at": time.time(),
        }

        self._check_log.append(result)
        return result

    def check_all(self, pins: List[PinterestPin]) -> Dict[str, Any]:
        results = [self.check_pin(p, pins) for p in pins]
        healthy = sum(1 for r in results if r["health_score"] >= 70)
        degraded = sum(1 for r in results if 40 <= r["health_score"] < 70)
        critical = sum(1 for r in results if r["health_score"] < 40)

        return {
            "total_checked": len(results),
            "healthy": healthy,
            "degraded": degraded,
            "critical": critical,
            "overall_score": round(sum(r["health_score"] for r in results) / max(len(results), 1), 1),
            "total_issues": sum(r["issue_count"] for r in results),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {"total_checks": len(self._check_log)}
