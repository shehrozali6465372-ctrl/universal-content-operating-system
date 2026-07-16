"""Compliance Engine — Core orchestrator for platform compliance checking.

Orchestrates format checking, content policy validation,
and multi-platform compliance analysis.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.platform_compliance_engine.format_checker import FormatChecker
from layers.layer06_quality.modules.platform_compliance_engine.content_policy_checker import ContentPolicyChecker
from layers.layer06_quality.modules.platform_compliance_engine.platform_rules import get_rules, get_all_platforms
from layers.layer06_quality.modules.platform_compliance_engine.compliance_report import (
    ComplianceReport, PlatformComplianceResult,
)


class ComplianceEngine:
    """Orchestrates full platform compliance pipeline."""

    def __init__(
        self,
        format_checker: Optional[FormatChecker] = None,
        policy_checker: Optional[ContentPolicyChecker] = None,
    ) -> None:
        self.format_checker = format_checker or FormatChecker()
        self.policy_checker = policy_checker or ContentPolicyChecker()
        self._check_count = 0

    def check(self, content: str, platform: str) -> PlatformComplianceResult:
        """Check content against a specific platform."""
        result = PlatformComplianceResult(platform=platform)
        rules = get_rules(platform)

        if not rules:
            result.is_compliant = False
            result.compliance_score = 0.0
            self._check_count += 1
            return result

        # Count total rules being checked
        result.total_rules = self._count_rules(rules)

        # Format checks
        format_violations = self.format_checker.check(content, rules)
        for v in format_violations:
            result.add_violation(v)

        # Content policy checks
        policy_violations = self.policy_checker.check(content, rules)
        for v in policy_violations:
            result.add_violation(v)

        result.compute_score()
        self._check_count += 1
        return result

    def check_batch(self, content: str, platforms: Optional[List[str]] = None) -> ComplianceReport:
        """Check content against multiple platforms."""
        report = ComplianceReport()
        start_time = time.time()

        target_platforms = platforms or get_all_platforms()
        for platform in target_platforms:
            result = self.check(content, platform)
            report.platform_results.append(result)

        report.compute_overall()
        elapsed = time.time() - start_time
        report.statistics["check_time_ms"] = round(elapsed * 1000, 2)

        self._check_count += 1
        return report

    def check_quick(self, content: str, platform: str = "facebook") -> Dict[str, Any]:
        """Quick compliance check returning summary."""
        result = self.check(content, platform)
        return {
            "platform": platform,
            "is_compliant": result.is_compliant,
            "compliance_score": result.compliance_score,
            "violation_count": len(result.violations),
            "auto_fixable": sum(1 for v in result.violations if v.auto_fixable),
        }

    def get_fixable_violations(self, result: PlatformComplianceResult) -> List:
        """Return only auto-fixable violations."""
        return [v for v in result.violations if v.auto_fixable]

    def _count_rules(self, rules: Dict) -> int:
        """Count how many rules are being checked."""
        count = 0
        if "max_post_length" in rules or "max_description_length" in rules:
            count += 1
        if "min_post_length" in rules:
            count += 1
        if "optimal_length" in rules or "optimal_caption_length" in rules:
            count += 1
        if "max_hashtags" in rules:
            count += 1
        if "max_mentions" in rules:
            count += 1
        if rules.get("no_engagement_bait"):
            count += 1
        if rules.get("no_all_caps"):
            count += 1
        if rules.get("professional_tone"):
            count += 1
        if rules.get("requires_hashtags"):
            count += 1
        if rules.get("forbidden_patterns"):
            count += len(rules["forbidden_patterns"])
        return max(1, count)

    @property
    def check_count(self) -> int:
        return self._check_count
