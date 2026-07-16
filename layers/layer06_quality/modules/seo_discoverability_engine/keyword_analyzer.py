"""Keyword Analyzer — Analyze keyword density, placement, and optimization.

Checks:
- Keyword density (optimal: 1-3%)
- Keyword in title/heading
- Keyword in first sentence
- Keyword distribution across content
- Keyword stuffing detection
"""
from __future__ import annotations
import re
from typing import List

from layers.layer06_quality.modules.seo_discoverability_engine.seo_report import KeywordResult, SEOIssue


_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "but", "or", "if", "this", "that", "these", "those", "it",
    "its", "not", "no", "so", "than", "too", "very", "just", "also",
}


class KeywordAnalyzer:
    """Analyze keyword usage and optimization in content."""

    OPTIMAL_DENSITY_MIN = 0.01
    OPTIMAL_DENSITY_MAX = 0.03
    STUFFING_THRESHOLD = 0.05

    def __init__(self) -> None:
        self._check_count = 0

    def analyze(
        self, content: str, keyword: str, title: str = "",
    ) -> KeywordResult:
        """Full keyword analysis."""
        result = KeywordResult()
        result.primary_keyword = keyword
        words = content.split()
        result.word_count = len(words)

        if not keyword or not words:
            return result

        # Count keyword occurrences
        keyword_lower = keyword.lower()
        content_lower = content.lower()
        result.keyword_count = content_lower.count(keyword_lower)
        result.keyword_density = result.keyword_count / max(1, result.word_count)

        # Title check
        if title:
            result.in_title = keyword_lower in title.lower()

        # First sentence check
        first_sentence = re.split(r'[.!?]', content)[0] if content else ""
        result.in_first_sentence = keyword_lower in first_sentence.lower()

        # Placement score
        result.keyword_placement_score = self._compute_placement_score(result)

        # Issues
        result.issues = self._find_issues(result)

        self._check_count += 1
        return result

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords from text by frequency."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq: dict = {}
        for w in words:
            if w not in _STOP_WORDS:
                word_freq[w] = word_freq.get(w, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_n]]

    def check_keyword_stuffing(self, content: str, keyword: str) -> bool:
        """Check if keyword is overused (stuffing)."""
        words = content.split()
        if not words:
            return False
        pattern = re.compile(r"\b" + re.escape(keyword.lower()) + r"\b")
        density = len(pattern.findall(content.lower())) / len(words)
        return density > self.STUFFING_THRESHOLD

    def _compute_placement_score(self, result: KeywordResult) -> float:
        """Compute keyword placement optimization score."""
        score = 0.0
        if result.keyword_count > 0:
            score += 0.3
        if result.in_title:
            score += 0.3
        if result.in_first_sentence:
            score += 0.2
        if self.OPTIMAL_DENSITY_MIN <= result.keyword_density <= self.OPTIMAL_DENSITY_MAX:
            score += 0.2
        elif result.keyword_density > 0:
            score += 0.1
        return min(1.0, score)

    def _find_issues(self, result: KeywordResult) -> List[SEOIssue]:
        """Find keyword-related SEO issues."""
        issues: List[SEOIssue] = []
        if result.keyword_count == 0:
            issues.append(SEOIssue(
                category="keyword", severity="high",
                description=f"Keyword '{result.primary_keyword}' not found in content",
                suggestion=f"Include '{result.primary_keyword}' naturally in the content",
                score_impact=-0.3,
            ))
        elif result.keyword_density > self.STUFFING_THRESHOLD:
            issues.append(SEOIssue(
                category="keyword_stuffing", severity="high",
                description=f"Keyword density {result.keyword_density:.1%} exceeds {self.STUFFING_THRESHOLD:.0%} threshold",
                suggestion="Reduce keyword frequency — aim for 1-3% density",
                score_impact=-0.25,
            ))
        elif result.keyword_density < self.OPTIMAL_DENSITY_MIN and result.keyword_count > 0:
            issues.append(SEOIssue(
                category="keyword_density", severity="medium",
                description=f"Keyword density {result.keyword_density:.2%} is below optimal 1%",
                suggestion="Include the keyword more frequently for better SEO",
                score_impact=-0.1,
            ))

        if not result.in_title and result.primary_keyword:
            issues.append(SEOIssue(
                category="keyword_placement", severity="medium",
                description="Primary keyword not found in title/heading",
                suggestion=f"Include '{result.primary_keyword}' in the title",
                score_impact=-0.15,
            ))

        if not result.in_first_sentence and result.primary_keyword:
            issues.append(SEOIssue(
                category="keyword_placement", severity="low",
                description="Primary keyword not in first sentence",
                suggestion="Consider mentioning the keyword early for better crawlability",
                score_impact=-0.05,
            ))

        return issues

    @property
    def check_count(self) -> int:
        return self._check_count
