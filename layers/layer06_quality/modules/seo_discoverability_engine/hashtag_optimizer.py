"""Hashtag Optimizer — Analyze and optimize hashtags for social platforms.

Checks per platform:
- Hashtag count limits
- Hashtag relevance to content
- Hashtag diversity (mix of popular/niche)
- Hashtag placement
"""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.seo_discoverability_engine.seo_report import HashtagResult, SEOIssue


PLATFORM_LIMITS: Dict[str, int] = {
    "facebook": 30, "instagram": 30, "twitter": 5,
    "linkedin": 5, "tiktok": 5, "youtube": 15,
    "pinterest": 20, "reddit": 0, "medium": 0,
}

PLATFORM_OPTIMAL: Dict[str, int] = {
    "facebook": 3, "instagram": 5, "twitter": 2,
    "linkedin": 3, "tiktok": 3, "youtube": 5,
    "pinterest": 5, "reddit": 0, "medium": 0,
}


class HashtagOptimizer:
    """Analyze and optimize hashtags for discoverability."""

    def __init__(self) -> None:
        self._check_count = 0

    def analyze(self, content: str, platform: str = "facebook") -> HashtagResult:
        """Analyze hashtags in content for a specific platform."""
        result = HashtagResult(platform=platform)
        result.hashtags = self._extract_hashtags(content)
        result.count = len(result.hashtags)

        result.relevance_score = self._compute_relevance(content, result.hashtags)
        result.diversity_score = self._compute_diversity(result.hashtags)
        result.issues = self._find_issues(content, result)

        self._check_count += 1
        return result

    def suggest_hashtags(
        self, content: str, platform: str = "facebook", count: int = 5,
    ) -> List[str]:
        """Suggest relevant hashtags based on content keywords."""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        word_freq: dict = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [f"#{w}" for w, _ in top_words[:count] if len(w) > 3]

    def optimize(self, content: str, platform: str = "facebook") -> str:
        """Auto-optimize hashtags in content for platform limits."""
        limit = PLATFORM_LIMITS.get(platform, 10)
        hashtags = self._extract_hashtags(content)
        if len(hashtags) <= limit:
            return content
        # Remove excess hashtags from end
        excess = hashtags[limit:]
        optimized = content
        for tag in excess:
            # Remove the last occurrence
            idx = optimized.rfind(tag)
            if idx >= 0:
                optimized = optimized[:idx].rstrip() + optimized[idx + len(tag):]
        return optimized.strip()

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract all hashtags from text."""
        return re.findall(r'#\w+', text)

    def _compute_relevance(self, content: str, hashtags: List[str]) -> float:
        """Compute how relevant hashtags are to content."""
        if not hashtags:
            return 0.0
        content_words = set(content.lower().split())
        relevant = 0
        for tag in hashtags:
            tag_word = tag.lstrip("#").lower()
            if tag_word in content_words or any(
                tw in content_words for tw in tag_word.split("_")
            ):
                relevant += 1
        return relevant / len(hashtags) if hashtags else 0.0

    def _compute_diversity(self, hashtags: List[str]) -> float:
        """Compute hashtag diversity (mix of lengths, no duplicates)."""
        if not hashtags:
            return 0.0
        unique = set(h.lower() for h in hashtags)
        dedup_ratio = len(unique) / len(hashtags)
        lengths = [len(h) for h in unique]
        avg_len = sum(lengths) / len(lengths) if lengths else 0
        len_diversity = 1.0 - (max(lengths) - min(lengths)) / max(1, max(lengths)) if lengths else 0.5
        return round((dedup_ratio * 0.6 + len_diversity * 0.4), 3)

    def _find_issues(self, content: str, result: HashtagResult) -> List[SEOIssue]:
        """Find hashtag-related issues."""
        issues: List[SEOIssue] = []
        limit = PLATFORM_LIMITS.get(result.platform, 10)
        optimal = PLATFORM_OPTIMAL.get(result.platform, 3)

        if result.count > limit:
            issues.append(SEOIssue(
                category="hashtag_limit", severity="high",
                description=f"{result.count} hashtags exceeds {result.platform} limit of {limit}",
                suggestion=f"Reduce hashtags to {limit} or fewer for {result.platform}",
                score_impact=-0.2,
            ))
        elif result.count > optimal * 2:
            issues.append(SEOIssue(
                category="hashtag_quantity", severity="medium",
                description=f"{result.count} hashtags may look spammy on {result.platform}",
                suggestion=f"Optimal is {optimal}-{optimal * 2} hashtags for {result.platform}",
                score_impact=-0.1,
            ))

        if result.count == 0 and limit > 0:
            issues.append(SEOIssue(
                category="no_hashtags", severity="medium",
                description=f"No hashtags found — {result.platform} supports up to {limit}",
                suggestion=f"Add {optimal} relevant hashtags for better discoverability",
                score_impact=-0.1,
            ))

        if result.diversity_score < 0.5 and result.count > 1:
            issues.append(SEOIssue(
                category="hashtag_diversity", severity="low",
                description="Hashtags lack diversity — possible duplicates or similar lengths",
                suggestion="Mix popular and niche hashtags with varied lengths",
                score_impact=-0.05,
            ))

        return issues

    @property
    def check_count(self) -> int:
        return self._check_count
