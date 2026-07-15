"""Content Optimizer — SEO, readability, and platform optimization."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


PLATFORM_OPTIMIZATIONS = {
    "facebook": {"max_length": 63206, "optimal_length": 400, "emoji_ok": True, "cta_required": True},
    "instagram": {"max_length": 2200, "optimal_length": 200, "emoji_ok": True, "cta_required": True},
    "twitter": {"max_length": 280, "optimal_length": 200, "emoji_ok": True, "cta_required": False},
    "linkedin": {"max_length": 3000, "optimal_length": 800, "emoji_ok": False, "cta_required": True},
    "tiktok": {"max_length": 2200, "optimal_length": 200, "emoji_ok": True, "cta_required": True},
    "youtube": {"max_length": 5000, "optimal_length": 1000, "emoji_ok": True, "cta_required": True},
}


class OptimizationResult:
    """Result of content optimization."""
    __slots__ = ("original_length", "optimized_text", "platform", "readability_score",
                 "seo_score", "improvements", "issues", "score")

    def __init__(self) -> None:
        self.original_length = 0
        self.optimized_text = ""
        self.platform = ""
        self.readability_score = 0.0
        self.seo_score = 0.0
        self.improvements: List[str] = []
        self.issues: List[str] = []
        self.score = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_length": self.original_length,
            "optimized_length": len(self.optimized_text),
            "platform": self.platform,
            "readability_score": round(self.readability_score, 3),
            "seo_score": round(self.seo_score, 3),
            "improvements": self.improvements,
            "issues": self.issues,
            "score": round(self.score, 1),
        }


class ContentOptimizer:
    """Optimizes content for SEO, readability, and platform constraints."""

    def __init__(self) -> None:
        self._opt_count = 0

    def optimize(self, text: str, platform: str = "facebook",
                 keywords: Optional[List[str]] = None) -> OptimizationResult:
        """Optimize content for the target platform."""
        result = OptimizationResult()
        result.original_length = len(text)
        result.platform = platform
        optimized = text

        # Readability
        result.readability_score = self._calculate_readability(text)

        # SEO
        result.seo_score = self._calculate_seo(text, keywords or [])

        # Platform-specific optimizations
        spec = PLATFORM_OPTIMIZATIONS.get(platform, PLATFORM_OPTIMIZATIONS["facebook"])
        if len(text) > spec["max_length"]:
            optimized = optimized[:spec["max_length"] - 3] + "..."
            result.improvements.append("Truncated to platform limit")
        elif len(text) < spec["optimal_length"] * 0.5:
            result.issues.append(f"Content may be too short for {platform}")

        # Remove excessive whitespace
        optimized = ' '.join(optimized.split())
        if optimized != text:
            result.improvements.append("Normalized whitespace")

        # Keyword density check
        if keywords:
            for kw in keywords[:3]:
                if kw.lower() not in text.lower():
                    result.issues.append(f"Keyword '{kw}' not found in content")

        result.optimized_text = optimized

        # Overall score
        result.score = (result.readability_score * 0.4 + result.seo_score * 0.3 +
                        max(0, 100 - len(result.issues) * 10) * 0.3)
        self._opt_count += 1
        return result

    def optimize_seo(self, text: str, focus_keyword: str,
                     secondary_keywords: Optional[List[str]] = None) -> OptimizationResult:
        """SEO-focused optimization."""
        result = self.optimize(text, "blog", keywords=[focus_keyword] + (secondary_keywords or []))
        # Check keyword in first 100 chars
        if focus_keyword.lower() in text[:100].lower():
            result.improvements.append("Focus keyword appears in opening")
        else:
            result.issues.append("Consider adding focus keyword to opening")
        return result

    def _calculate_readability(self, text: str) -> float:
        words = text.split()
        sentences = max(text.count('.') + text.count('!') + text.count('?'), 1)
        avg_sentence_len = len(words) / sentences
        if avg_sentence_len < 15:
            return 0.9
        if avg_sentence_len < 25:
            return 0.7
        return 0.5

    def _calculate_seo(self, text: str, keywords: List[str]) -> float:
        if not keywords:
            return 0.5
        text_lower = text.lower()
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        return round(found / max(len(keywords), 1), 3)

    @property
    def optimization_count(self) -> int:
        return self._opt_count
