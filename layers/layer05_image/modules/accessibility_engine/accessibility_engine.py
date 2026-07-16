"""Accessibility Engine — Alt text, contrast validation, readability checks."""
from __future__ import annotations
from typing import Any, Dict, List


class AccessibilityResult:
    __slots__ = ("alt_text", "contrast_score", "text_readability",
                 "issues", "score", "recommendations")

    def __init__(self) -> None:
        self.alt_text = ""
        self.contrast_score = 1.0
        self.text_readability = 1.0
        self.issues: List[str] = []
        self.score = 100.0
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alt_text": self.alt_text,
            "contrast_score": round(self.contrast_score, 3),
            "text_readability": round(self.text_readability, 3),
            "issues": self.issues,
            "score": round(self.score, 1),
            "recommendations": self.recommendations,
        }


class AccessibilityEngine:
    def __init__(self) -> None:
        self._check_count = 0

    def generate_alt_text(self, topic: str, image_type: str = "photo",
                          description: str = "") -> str:
        parts = [f"{image_type.title()}"]
        if description:
            parts.append(f"showing {description[:80]}")
        parts.append(f"about {topic}")
        return " ".join(parts)

    def check_contrast(self, bg_color: str = "#FFFFFF", text_color: str = "#000000") -> float:
        bg_lum = self._relative_luminance(bg_color)
        text_lum = self._relative_luminance(text_color)
        lighter = max(bg_lum, text_lum)
        darker = min(bg_lum, text_lum)
        return round((lighter + 0.05) / (darker + 0.05), 2)

    def check_text_density(self, text: str, image_area: int = 1000000) -> AccessibilityResult:
        result = AccessibilityResult()
        density = len(text) / image_area * 10000
        if density > 0.05:
            result.issues.append("Text density too high")
            result.score -= 20
        result.recommendations.append("Ensure text is at least 24pt")
        self._check_count += 1
        return result

    def validate(self, text_overlay: str = "", bg_color: str = "#FFFFFF",
                 text_color: str = "#000000", topic: str = "") -> AccessibilityResult:
        result = AccessibilityResult()
        result.alt_text = self.generate_alt_text(topic, description=text_overlay[:50])
        result.contrast_score = self.check_contrast(bg_color, text_color)
        if result.contrast_score < 4.5:
            result.issues.append(f"Low contrast: {result.contrast_score}")
            result.score -= 25
        if text_overlay:
            words = text_overlay.split()
            if len(words) > 15:
                result.issues.append("Too much text — keep under 15 words")
                result.score -= 15
        self._check_count += 1
        return result

    def _relative_luminance(self, hex_color: str) -> float:
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return 0.5
        r, g, b = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @property
    def check_count(self) -> int:
        return self._check_count
