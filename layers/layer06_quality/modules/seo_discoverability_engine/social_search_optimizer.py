"""Social Search Optimizer — Platform-specific discoverability checks.

Each platform has unique search algorithms and discoverability signals.
This module checks content against each platform's optimization rules.
"""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.seo_discoverability_engine.seo_report import PlatformDiscoverability, SEOIssue


PLATFORM_RULES: Dict[str, Dict] = {
    "google": {
        "checks": ["keyword_in_title", "keyword_in_first_100_words", "meta_description", "headings", "internal_links"],
        "optimal_word_count": (300, 2000),
        "requires": ["title", "description"],
    },
    "instagram": {
        "checks": ["hashtags", "location", "mentions", "alt_text", "caption_length"],
        "optimal_hashtags": (3, 10),
        "max_caption": 2200,
        "requires": ["hashtags"],
    },
    "tiktok": {
        "checks": ["hashtags", "trending_audio", "caption_length", "keywords_in_caption"],
        "optimal_hashtags": (3, 5),
        "max_caption": 2200,
        "requires": ["hashtags"],
    },
    "youtube": {
        "checks": ["title_keyword", "description_keyword", "tags", "timestamps", "thumbnail"],
        "optimal_title_length": (40, 60),
        "optimal_desc_length": (200, 5000),
        "requires": ["title", "description"],
    },
    "facebook": {
        "checks": ["engagement_hooks", "shareability", "link_preview", "hashtags"],
        "optimal_length": (40, 80),
        "requires": [],
    },
    "linkedin": {
        "checks": ["professional_tone", "hashtags", "mentions", "article_format"],
        "optimal_hashtags": (3, 5),
        "max_length": 3000,
        "requires": [],
    },
    "pinterest": {
        "checks": ["keyword_rich_description", "vertical_image", "board_relevance"],
        "optimal_desc_length": (100, 500),
        "requires": ["description"],
    },
}


class SocialSearchOptimizer:
    """Optimize content discoverability for social platforms."""

    def __init__(self) -> None:
        self._check_count = 0

    def optimize(self, content: str, platform: str, keyword: str = "") -> PlatformDiscoverability:
        """Check and score content for a specific platform."""
        result = PlatformDiscoverability(platform=platform)
        rules = PLATFORM_RULES.get(platform.lower())

        if not rules:
            result.score = 0.5
            result.issues.append(SEOIssue(
                category="unknown_platform", severity="medium",
                description=f"No optimization rules for '{platform}'",
                suggestion="Add platform-specific rules to PLATFORM_RULES",
            ))
            result.compute_level()
            self._check_count += 1
            return result

        checks = rules.get("checks", [])
        score = 0.0
        check_weight = 1.0 / max(1, len(checks))

        for check in checks:
            passed = self._run_check(content, check, keyword, rules)
            if passed:
                score += check_weight

        result.score = round(min(1.0, score), 3)

        # Platform-specific issues
        self._check_length(content, rules, result)
        if keyword:
            self._check_keyword_in_content(content, keyword, result)

        result.compute_level()
        self._check_count += 1
        return result

    def optimize_all(self, content: str, keyword: str = "") -> List[PlatformDiscoverability]:
        """Optimize for all known platforms."""
        return [
            self.optimize(content, platform, keyword)
            for platform in PLATFORM_RULES
        ]

    def get_best_platforms(self, results: List[PlatformDiscoverability]) -> List[str]:
        """Return platforms where content is well-optimized."""
        return [r.platform for r in results if r.optimization_level in ("excellent", "good")]

    def _run_check(
        self, content: str, check: str, keyword: str, rules: Dict,
    ) -> bool:
        """Run a single platform check."""
        content_lower = content.lower()
        if check == "keyword_in_title":
            return keyword.lower() in content_lower[:100] if keyword else True
        if check == "keyword_in_first_100_words":
            words = content.split()[:100]
            return keyword.lower() in " ".join(words).lower() if keyword else True
        if check == "hashtags":
            return bool(re.search(r'#\w+', content))
        if check == "mentions":
            return bool(re.search(r'@\w+', content))
        if check == "meta_description":
            return len(content) > 100
        if check == "headings":
            return bool(re.search(r'^#+\s', content, re.MULTILINE))
        if check == "internal_links":
            return bool(re.search(r'https?://', content))
        if check in ("caption_length", "optimal_length"):
            return 20 <= len(content.split()) <= 500
        if check == "professional_tone":
            caps = sum(1 for w in content.split() if w.isupper() and len(w) > 1)
            return caps / max(1, len(content.split())) < 0.3
        if check == "timestamps":
            return bool(re.search(r'\d+:\d+', content))
        if check in ("engagement_hooks", "shareability"):
            return bool(re.search(r'\?|!|"', content))
        return True

    def _check_length(self, content: str, rules: Dict, result: PlatformDiscoverability) -> None:
        max_len = rules.get("max_length") or rules.get("max_caption")
        if max_len and len(content) > max_len:
            result.issues.append(SEOIssue(
                category="length", severity="high",
                description=f"Content exceeds {result.platform} limit ({len(content)}/{max_len})",
                suggestion=f"Shorten content to under {max_len} characters",
                score_impact=-0.2,
            ))
            result.suggestions.append(f"Shorten to {max_len} chars")

    def _check_keyword_in_content(
        self, content: str, keyword: str, result: PlatformDiscoverability,
    ) -> None:
        if keyword.lower() not in content.lower():
            result.issues.append(SEOIssue(
                category="keyword", severity="medium",
                description=f"Keyword '{keyword}' not found in content",
                suggestion=f"Include '{keyword}' for better discoverability on {result.platform}",
                score_impact=-0.1,
            ))
            result.suggestions.append(f"Add keyword '{keyword}' to content")

    @property
    def check_count(self) -> int:
        return self._check_count
