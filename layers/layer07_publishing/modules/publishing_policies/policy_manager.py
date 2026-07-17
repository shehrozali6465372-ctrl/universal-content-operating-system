"""Policy Manager — Orchestrate all publishing policies."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.publishing_policies.platform_rules import PlatformRules
from layers.layer07_publishing.modules.publishing_policies.content_limits import ContentLimits
from layers.layer07_publishing.modules.publishing_policies.rate_limiter import RateLimiter
from layers.layer07_publishing.modules.publishing_policies.media_policies import MediaPolicies
from layers.layer07_publishing.modules.publishing_policies.content_safety import ContentSafety
from layers.layer07_publishing.modules.publishing_policies.brand_safety import BrandSafety
from layers.layer07_publishing.modules.publishing_policies.schedule_policies import SchedulePolicies
from layers.layer07_publishing.modules.publishing_policies.api_versions import APIVersionManager
from layers.layer07_publishing.modules.publishing_policies.policy_validator import PolicyValidator, ValidationResult

_MANAGER_COUNTER = itertools.count(1)


class PolicyReport:
    """Comprehensive policy compliance report."""

    __slots__ = ("report_id", "platform", "validation", "rate_remaining",
                 "api_supported", "timestamp")

    def __init__(self, platform: str = "") -> None:
        self.report_id: str = f"prpt_{next(_MANAGER_COUNTER)}"
        self.platform = platform
        self.validation: Optional[ValidationResult] = None
        self.rate_remaining: int = 0
        self.api_supported: bool = True
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "platform": self.platform,
            "passed": self.validation.passed if self.validation else True,
            "violations": self.validation.violations if self.validation else [],
            "rate_remaining": self.rate_remaining,
            "api_supported": self.api_supported,
            "timestamp": self.timestamp,
        }


class PolicyManager:
    """Orchestrate all publishing policies.

    Single entry point for all policy checks.
    """

    def __init__(self) -> None:
        self.platform_rules = PlatformRules()
        self.content_limits = ContentLimits()
        self.rate_limiter = RateLimiter()
        self.media_policies = MediaPolicies()
        self.content_safety = ContentSafety()
        self.brand_safety = BrandSafety()
        self.schedule_policies = SchedulePolicies()
        self.api_versions = APIVersionManager()
        self.validator = PolicyValidator()
        self._reports: List[PolicyReport] = []

    def validate_content(
        self, platform: str, content: str, **kwargs: Any
    ) -> ValidationResult:
        result = self.validator.validate(platform, content, **kwargs)
        report = PolicyReport(platform)
        report.validation = result
        report.rate_remaining = self.rate_limiter.get_remaining(platform)
        report.api_supported = self.api_versions.is_supported(platform)
        self._reports.append(report)
        return result

    def is_publish_allowed(self, platform: str) -> bool:
        return (
            self.rate_limiter.can_publish(platform)
            and self.api_versions.is_supported(platform)
        )

    def record_publish(self, platform: str) -> None:
        self.rate_limiter.record_publish(platform)

    def get_platform_info(self, platform: str) -> Dict[str, Any]:
        return {
            "platform": platform,
            "rules_count": self.platform_rules.get_rules_count(platform),
            "limits": self.content_limits.get_limits(platform),
            "rate_remaining": self.rate_limiter.get_remaining(platform),
            "api_supported": self.api_versions.is_supported(platform),
            "media_policy": self.media_policies.get_policy(platform).to_dict(),
            "schedule_policy": self.schedule_policies.get_policy(platform).to_dict(),
        }

    def get_all_platforms(self) -> List[str]:
        return self.content_limits.get_supported_platforms()

    def get_reports(self, platform: str = "") -> List[PolicyReport]:
        if platform:
            return [r for r in self._reports if r.platform == platform]
        return list(self._reports)

    @property
    def report_count(self) -> int:
        return len(self._reports)
