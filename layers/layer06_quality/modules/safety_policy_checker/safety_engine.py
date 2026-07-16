"""Safety Engine — Core orchestrator for safety and policy checking.

Orchestrates harmful content detection, spam detection, platform policy checks,
and copyright verification. Produces a SafetyReport.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.safety_policy_checker.harmful_content_detector import HarmfulContentDetector
from layers.layer06_quality.modules.safety_policy_checker.spam_detector import SpamDetector
from layers.layer06_quality.modules.safety_policy_checker.platform_policy_checker import PlatformPolicyChecker
from layers.layer06_quality.modules.safety_policy_checker.safety_report import SafetyReport


class SafetyEngine:
    """Orchestrates full safety and policy validation pipeline."""

    def __init__(
        self,
        harmful_detector: Optional[HarmfulContentDetector] = None,
        spam_detector: Optional[SpamDetector] = None,
        policy_checker: Optional[PlatformPolicyChecker] = None,
    ) -> None:
        self.harmful_detector = harmful_detector or HarmfulContentDetector()
        self.spam_detector = spam_detector or SpamDetector()
        self.policy_checker = policy_checker or PlatformPolicyChecker()
        self._check_count = 0

    def check(
        self,
        content: str,
        platforms: Optional[List[str]] = None,
    ) -> SafetyReport:
        """Full safety check pipeline."""
        report = SafetyReport()
        start_time = time.time()

        # Step 1: Harmful content detection
        harmful_flags = self.harmful_detector.detect(content)
        report.harmful_content_flags = harmful_flags
        for flag in harmful_flags:
            report.add_flag(flag)

        # Step 2: Spam detection
        spam_flags = self.spam_detector.detect(content)
        report.spam_flags = spam_flags
        for flag in spam_flags:
            report.add_flag(flag)

        # Step 3: Platform policy checks
        if platforms:
            for platform in platforms:
                result = self.policy_checker.check(content, platform)
                report.policy_results.append(result)
                for flag in result.flags:
                    report.add_flag(flag)

        # Step 4: Compute overall
        report.compute_overall()

        elapsed = time.time() - start_time
        report.statistics["check_time_ms"] = round(elapsed * 1000, 2)
        report.statistics["content_length"] = len(content)

        self._check_count += 1
        return report

    def check_quick(self, content: str) -> Dict[str, Any]:
        """Quick safety check returning summary dict."""
        report = self.check(content)
        return {
            "overall_safe": report.overall_safe,
            "overall_score": report.overall_score,
            "harmful_flags": len(report.harmful_content_flags),
            "spam_flags": len(report.spam_flags),
            "critical_flags": report.statistics.get("critical_flags", 0),
            "high_flags": report.statistics.get("high_flags", 0),
        }

    def check_batch(
        self, contents: List[str], platforms: Optional[List[str]] = None,
    ) -> List[SafetyReport]:
        """Check multiple content pieces."""
        return [self.check(c, platforms) for c in contents]

    @property
    def check_count(self) -> int:
        return self._check_count
