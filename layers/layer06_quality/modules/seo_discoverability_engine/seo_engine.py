"""SEO Engine — Core orchestrator for SEO and discoverability checks.

Orchestrates keyword analysis, hashtag optimization, metadata checks,
and platform-specific discoverability scoring.
"""
from __future__ import annotations
import time
from typing import Any, Dict, Optional

from layers.layer06_quality.modules.seo_discoverability_engine.keyword_analyzer import KeywordAnalyzer
from layers.layer06_quality.modules.seo_discoverability_engine.hashtag_optimizer import HashtagOptimizer
from layers.layer06_quality.modules.seo_discoverability_engine.metadata_checker import MetadataChecker
from layers.layer06_quality.modules.seo_discoverability_engine.social_search_optimizer import SocialSearchOptimizer
from layers.layer06_quality.modules.seo_discoverability_engine.seo_report import SEODiscoverabilityReport


class SEOEngine:
    """Orchestrates full SEO and discoverability pipeline."""

    def __init__(
        self,
        keyword_analyzer: Optional[KeywordAnalyzer] = None,
        hashtag_optimizer: Optional[HashtagOptimizer] = None,
        metadata_checker: Optional[MetadataChecker] = None,
        social_optimizer: Optional[SocialSearchOptimizer] = None,
    ) -> None:
        self.keyword_analyzer = keyword_analyzer or KeywordAnalyzer()
        self.hashtag_optimizer = hashtag_optimizer or HashtagOptimizer()
        self.metadata_checker = metadata_checker or MetadataChecker()
        self.social_optimizer = social_optimizer or SocialSearchOptimizer()
        self._check_count = 0

    def check(
        self,
        content: str,
        keyword: str = "",
        title: str = "",
        description: str = "",
        platform: str = "facebook",
    ) -> SEODiscoverabilityReport:
        """Full SEO check pipeline."""
        report = SEODiscoverabilityReport()
        start_time = time.time()

        # Step 1: Keyword analysis
        report.keyword_result = self.keyword_analyzer.analyze(content, keyword, title)

        # Step 2: Hashtag analysis
        report.hashtag_result = self.hashtag_optimizer.analyze(content, platform)

        # Step 3: Metadata check
        report.metadata_result = self.metadata_checker.full_check(title, description, content)

        # Step 4: Platform discoverability
        platform_result = self.social_optimizer.optimize(content, platform, keyword)
        report.platform_results.append(platform_result)

        # Collect all issues
        if report.keyword_result:
            report.issues.extend(report.keyword_result.issues)
        if report.hashtag_result:
            report.issues.extend(report.hashtag_result.issues)
        if report.metadata_result:
            report.issues.extend(report.metadata_result.issues)
        report.issues.extend(platform_result.issues)

        # Compute overall
        report.compute_overall()

        elapsed = time.time() - start_time
        report.statistics["check_time_ms"] = round(elapsed * 1000, 2)
        report.statistics["content_length"] = len(content)
        report.statistics["keyword"] = keyword
        report.statistics["platform"] = platform

        self._check_count += 1
        return report

    def check_quick(self, content: str, keyword: str = "") -> Dict[str, Any]:
        """Quick SEO check returning summary dict."""
        report = self.check(content, keyword=keyword)
        return {
            "overall_score": report.overall_score,
            "keyword_score": report.keyword_result.keyword_placement_score if report.keyword_result else 0,
            "hashtag_score": report.hashtag_result.relevance_score if report.hashtag_result else 0,
            "metadata_score": (report.metadata_result.title_score + report.metadata_result.description_score) / 2 if report.metadata_result else 0,
            "issue_count": len(report.issues),
            "platform_optimized": report.platform_results[0].optimization_level if report.platform_results else "unknown",
        }

    def check_multi_platform(
        self, content: str, keyword: str = "", title: str = "", description: str = "",
    ) -> SEODiscoverabilityReport:
        """Check content across all platforms."""
        report = SEODiscoverabilityReport()
        start_time = time.time()

        report.keyword_result = self.keyword_analyzer.analyze(content, keyword, title)
        report.metadata_result = self.metadata_checker.full_check(title, description, content)

        all_platforms = self.social_optimizer.optimize_all(content, keyword)
        report.platform_results = all_platforms

        # Use first platform's hashtag result as representative
        report.hashtag_result = self.hashtag_optimizer.analyze(content, "facebook")

        report.compute_overall()
        elapsed = time.time() - start_time
        report.statistics["check_time_ms"] = round(elapsed * 1000, 2)
        report.statistics["platforms_checked"] = len(all_platforms)

        self._check_count += 1
        return report

    @property
    def check_count(self) -> int:
        return self._check_count
