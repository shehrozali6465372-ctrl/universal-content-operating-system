"""SEO Report — Result models for SEO and discoverability checking."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class SEOIssue:
    """A single SEO issue found in content."""

    __slots__ = ("category", "severity", "description", "suggestion",
                 "score_impact")

    def __init__(
        self,
        category: str = "",
        severity: str = "low",
        description: str = "",
        suggestion: str = "",
        score_impact: float = 0.0,
    ) -> None:
        self.category = category
        self.severity = severity
        self.description = description
        self.suggestion = suggestion
        self.score_impact = max(-1.0, min(0.0, score_impact))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion,
            "score_impact": round(self.score_impact, 3),
        }


class KeywordResult:
    """Result of keyword analysis."""

    __slots__ = (
        "primary_keyword", "keyword_density", "keyword_count",
        "word_count", "in_title", "in_first_sentence",
        "keyword_placement_score", "issues",
    )

    def __init__(self) -> None:
        self.primary_keyword = ""
        self.keyword_density = 0.0
        self.keyword_count = 0
        self.word_count = 0
        self.in_title = False
        self.in_first_sentence = False
        self.keyword_placement_score = 0.0
        self.issues: List[SEOIssue] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_keyword": self.primary_keyword,
            "keyword_density": round(self.keyword_density, 4),
            "keyword_count": self.keyword_count,
            "word_count": self.word_count,
            "in_title": self.in_title,
            "in_first_sentence": self.in_first_sentence,
            "keyword_placement_score": round(self.keyword_placement_score, 3),
            "issues": [i.to_dict() for i in self.issues],
        }


class HashtagResult:
    """Result of hashtag analysis."""

    __slots__ = (
        "platform", "hashtags", "count", "relevance_score",
        "diversity_score", "issues",
    )

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.hashtags: List[str] = []
        self.count = 0
        self.relevance_score = 0.0
        self.diversity_score = 0.0
        self.issues: List[SEOIssue] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "hashtags": self.hashtags,
            "count": self.count,
            "relevance_score": round(self.relevance_score, 3),
            "diversity_score": round(self.diversity_score, 3),
            "issues": [i.to_dict() for i in self.issues],
        }


class MetadataResult:
    """Result of metadata analysis."""

    __slots__ = (
        "title_score", "description_score", "alt_text_score",
        "has_url", "has_cta", "issues",
    )

    def __init__(self) -> None:
        self.title_score = 0.0
        self.description_score = 0.0
        self.alt_text_score = 0.0
        self.has_url = False
        self.has_cta = False
        self.issues: List[SEOIssue] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title_score": round(self.title_score, 3),
            "description_score": round(self.description_score, 3),
            "alt_text_score": round(self.alt_text_score, 3),
            "has_url": self.has_url,
            "has_cta": self.has_cta,
            "issues": [i.to_dict() for i in self.issues],
        }


class PlatformDiscoverability:
    """Discoverability score for a specific platform."""

    __slots__ = ("platform", "score", "optimization_level",
                 "issues", "suggestions")

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.score = 0.0
        self.optimization_level = "unknown"
        self.issues: List[SEOIssue] = []
        self.suggestions: List[str] = []

    def compute_level(self) -> None:
        if self.score >= 0.85:
            self.optimization_level = "excellent"
        elif self.score >= 0.7:
            self.optimization_level = "good"
        elif self.score >= 0.5:
            self.optimization_level = "fair"
        else:
            self.optimization_level = "poor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "score": round(self.score, 3),
            "optimization_level": self.optimization_level,
            "issue_count": len(self.issues),
            "suggestions": self.suggestions,
        }


class SEODiscoverabilityReport:
    """Complete SEO and discoverability report."""

    __slots__ = (
        "overall_score", "keyword_result", "hashtag_result",
        "metadata_result", "platform_results", "issues",
        "statistics",
    )

    def __init__(self) -> None:
        self.overall_score = 0.0
        self.keyword_result: Optional[KeywordResult] = None
        self.hashtag_result: Optional[HashtagResult] = None
        self.metadata_result: Optional[MetadataResult] = None
        self.platform_results: List[PlatformDiscoverability] = []
        self.issues: List[SEOIssue] = []
        self.statistics: Dict[str, Any] = {}

    def compute_overall(self) -> None:
        """Compute overall SEO score from all components."""
        scores = []
        if self.keyword_result:
            scores.append(self.keyword_result.keyword_placement_score * 0.35)
        if self.hashtag_result:
            scores.append(self.hashtag_result.relevance_score * 0.25)
        if self.metadata_result:
            meta_avg = (self.metadata_result.title_score +
                        self.metadata_result.description_score) / 2
            scores.append(meta_avg * 0.25)
        if self.platform_results:
            platform_avg = sum(p.score for p in self.platform_results) / len(self.platform_results)
            scores.append(platform_avg * 0.15)

        self.overall_score = round(sum(scores), 3) if scores else 0.0

        self.statistics = {
            "overall_score": self.overall_score,
            "issue_count": len(self.issues),
            "platforms_checked": len(self.platform_results),
            "platforms_optimized": sum(1 for p in self.platform_results if p.optimization_level in ("excellent", "good")),
        }

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        return {
            "overall_score": self.overall_score,
            "keyword_result": self.keyword_result.to_dict() if self.keyword_result else None,
            "hashtag_result": self.hashtag_result.to_dict() if self.hashtag_result else None,
            "metadata_result": self.metadata_result.to_dict() if self.metadata_result else None,
            "platform_results": [p.to_dict() for p in self.platform_results],
            "issues": [i.to_dict() for i in self.issues],
            "statistics": self.statistics,
        }
