"""Metadata Checker — Validate content metadata for discoverability.

Checks:
- Title quality (length, keyword, power words)
- Description quality
- URL/link presence
- CTA presence
- Alt text recommendations
"""
from __future__ import annotations
import re

from layers.layer06_quality.modules.seo_discoverability_engine.seo_report import MetadataResult, SEOIssue


POWER_WORDS = {
    "ultimate", "essential", "proven", "complete", "guide", "secret",
    "free", "best", "top", "easy", "quick", "simple", "powerful",
    "exclusive", "discover", "unlock", "transform", "boost", "master",
}


class MetadataChecker:
    """Validate content metadata for SEO and discoverability."""

    OPTIMAL_TITLE_MIN = 30
    OPTIMAL_TITLE_MAX = 60
    OPTIMAL_DESC_MIN = 120
    OPTIMAL_DESC_MAX = 160

    def __init__(self) -> None:
        self._check_count = 0

    def check_title(self, title: str) -> float:
        """Check title quality and return score."""
        score = 0.0
        if not title:
            return 0.0

        length = len(title)
        if self.OPTIMAL_TITLE_MIN <= length <= self.OPTIMAL_TITLE_MAX:
            score += 0.4
        elif length > 0:
            score += 0.2

        if any(pw in title.lower() for pw in POWER_WORDS):
            score += 0.2

        if re.search(r'\d+', title):
            score += 0.1

        if title[0].isupper():
            score += 0.1

        if not title.endswith((".", "!", "?")):
            score += 0.1

        words = title.split()
        if 5 <= len(words) <= 12:
            score += 0.1

        return min(1.0, score)

    def check_description(self, description: str) -> float:
        """Check meta description quality."""
        score = 0.0
        if not description:
            return 0.0

        length = len(description)
        if self.OPTIMAL_DESC_MIN <= length <= self.OPTIMAL_DESC_MAX:
            score += 0.5
        elif length > 50:
            score += 0.3
        elif length > 0:
            score += 0.1

        if any(pw in description.lower() for pw in POWER_WORDS):
            score += 0.2

        if re.search(r'\d+', description):
            score += 0.1

        sentences = description.split(".")
        if 1 <= len(sentences) <= 3:
            score += 0.1

        return min(1.0, score)

    def check_alt_text(self, text: str) -> float:
        """Check if alt text recommendations apply."""
        score = 0.5  # Default neutral
        if re.search(r'<img\b', text, re.IGNORECASE):
            if 'alt=' in text.lower():
                score = 0.8
            else:
                score = 0.2
        return score

    def full_check(
        self, title: str = "", description: str = "",
        content: str = "",
    ) -> MetadataResult:
        """Full metadata check."""
        result = MetadataResult()
        result.title_score = self.check_title(title)
        result.description_score = self.check_description(description)
        result.alt_text_score = self.check_alt_text(content)
        result.has_url = bool(re.search(r'https?://', content))
        result.has_cta = bool(re.search(
            r'\b(?:learn\s+more|sign\s+up|get\s+started|click\s+here|'
            r'shop\s+now|download|subscribe|follow|join|try)\b',
            content, re.IGNORECASE,
        ))

        if not title:
            result.issues.append(SEOIssue(
                category="metadata", severity="high",
                description="No title provided",
                suggestion="Add a descriptive title with primary keyword",
                score_impact=-0.3,
            ))
        elif result.title_score < 0.5:
            result.issues.append(SEOIssue(
                category="metadata", severity="medium",
                description="Title could be more SEO-optimized",
                suggestion="Add power words, keep 30-60 chars, include keyword",
                score_impact=-0.1,
            ))

        if not description:
            result.issues.append(SEOIssue(
                category="metadata", severity="medium",
                description="No description provided",
                suggestion="Add a meta description (120-160 chars)",
                score_impact=-0.2,
            ))

        if not result.has_url and content:
            result.issues.append(SEOIssue(
                category="metadata", severity="low",
                description="No URL found in content",
                suggestion="Include relevant links for better SEO",
                score_impact=-0.05,
            ))

        self._check_count += 1
        return result

    @property
    def check_count(self) -> int:
        return self._check_count
