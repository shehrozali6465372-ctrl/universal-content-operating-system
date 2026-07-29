"""PinOptimizer — AI-driven optimization: improve low-CTR pins, weak titles, poor descriptions."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin


class PinOptimizer:
    """AI-powered pin optimizer — analyzes performance and suggests improvements."""

    TITLE_IMPROVEMENTS = [
        "Add numbers (e.g., '10 Ideas', '5 Tips')",
        "Include power words (amazing, essential, ultimate)",
        "Add emojis for visual appeal",
        "Include year (e.g., '2026')",
        "Add 'You Need to See' or 'Must Try'",
        "Use question format",
        "Add 'Complete Guide' or 'Ultimate'",
    ]

    DESCRIPTION_IMPROVEMENTS = [
        "Add more keywords in first 2 lines",
        "Include a call-to-action",
        "Add line breaks for readability",
        "Mention specific numbers or stats",
        "Include hashtags at the end",
    ]

    def __init__(self) -> None:
        self._optimization_log: List[dict] = []

    def analyze_pin(self, pin: PinterestPin, ctr: float = 0.0) -> Dict[str, Any]:
        """Analyze a pin and suggest improvements."""
        suggestions: List[str] = []
        priority = "low"

        # Title analysis
        if len(pin.pin_title) < 20:
            suggestions.append(f"Short title ({len(pin.pin_title)} chars). {random.choice(self.TITLE_IMPROVEMENTS)}")
        if pin.pin_title.islower():
            suggestions.append("Capitalize first letter of each word")

        # Description analysis
        if not pin.pin_description:
            suggestions.append("Add a description with keywords")
        elif len(pin.pin_description) < 100:
            suggestions.append(f"Description too short ({len(pin.pin_description)} chars). Expand to 300+ chars")

        # Keywords
        if not pin.seo_keywords:
            suggestions.append("Add SEO keywords to improve search visibility")

        # Hashtags
        if not pin.hashtags:
            suggestions.append("Add hashtags for better discoverability")

        # Image alt text
        if not pin.alt_text:
            suggestions.append("Add alt text for accessibility and SEO")

        # CTR-based suggestions
        if ctr > 0 and ctr < 0.5:
            suggestions.append(f"Low CTR ({ctr}%). Consider better title and image")
            priority = "high"
        elif ctr > 2:
            suggestions.append("Pin is performing well")
            priority = "low"

        result = {
            "pin_id": pin.pin_id,
            "priority": priority,
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
        }

        self._optimization_log.append(result)
        return result

    def suggest_improvements(self, pin: PinterestPin) -> Dict[str, Any]:
        """Get actionable improvement suggestions for a pin."""
        return self.analyze_pin(pin, pin.ctr)

    def batch_analyze(self, pins: List[PinterestPin]) -> List[Dict[str, Any]]:
        """Analyze multiple pins and return prioritized list."""
        results = [self.analyze_pin(p, p.ctr) for p in pins]
        return sorted(results, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["priority"], 3))

    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyzed": len(self._optimization_log)}
