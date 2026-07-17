"""Policy Validator — Validate content against all policies."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.publishing_policies.content_limits import ContentLimits
from layers.layer07_publishing.modules.publishing_policies.media_policies import MediaPolicies
from layers.layer07_publishing.modules.publishing_policies.rate_limiter import RateLimiter
from layers.layer07_publishing.modules.publishing_policies.content_safety import ContentSafety
from layers.layer07_publishing.modules.publishing_policies.brand_safety import BrandSafety
from layers.layer07_publishing.modules.publishing_policies.schedule_policies import SchedulePolicies


class ValidationResult:
    """Result of a policy validation."""

    __slots__ = ("passed", "violations", "warnings", "platform")

    def __init__(self, platform: str = "") -> None:
        self.passed: bool = True
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self.platform = platform

    def add_violation(self, message: str) -> None:
        self.violations.append(message)
        self.passed = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "warnings": self.warnings,
            "platform": self.platform,
            "violation_count": len(self.violations),
            "warning_count": len(self.warnings),
        }


class PolicyValidator:
    """Validate content against all platform policies."""

    def __init__(self) -> None:
        self.content_limits = ContentLimits()
        self.media_policies = MediaPolicies()
        self.rate_limiter = RateLimiter()
        self.content_safety = ContentSafety()
        self.brand_safety = BrandSafety()
        self.schedule_policies = SchedulePolicies()
        self._validation_count = 0

    def validate(self, platform: str, content: str, **kwargs: Any) -> ValidationResult:
        result = ValidationResult(platform)

        # Text length
        if not self.content_limits.check_text_length(platform, content):
            max_len = self.content_limits.get_limit(platform, "max_text_length", 0)
            result.add_violation(f"Content exceeds max length {max_len}")

        # Content safety
        safety_violations = self.content_safety.check_content(content)
        for v in safety_violations:
            result.add_violation(f"Safety violation: {v.category}")

        # Rate limiting
        if not self.rate_limiter.can_publish(platform):
            result.add_violation("Rate limit exceeded")

        # Brand safety
        brand_id = kwargs.get("brand_id", "")
        if brand_id:
            brand_violations = self.brand_safety.check_content(brand_id, content)
            for v in brand_violations:
                result.add_violation(f"Brand safety: {v}")

        # Image count
        image_count = kwargs.get("image_count", 0)
        if image_count > 0 and not self.content_limits.check_image_count(platform, image_count):
            result.add_violation(f"Too many images: {image_count}")

        # Hashtag count
        hashtag_count = kwargs.get("hashtag_count", 0)
        if hashtag_count > 0 and not self.content_limits.check_hashtag_count(platform, hashtag_count):
            result.add_warning(f"Many hashtags: {hashtag_count}")

        self._validation_count += 1
        return result

    def validate_all_platforms(self, content: str, **kwargs: Any) -> Dict[str, ValidationResult]:
        results: Dict[str, ValidationResult] = {}
        for platform in self.content_limits.get_supported_platforms():
            results[platform] = self.validate(platform, content, **kwargs)
        return results

    @property
    def validation_count(self) -> int:
        return self._validation_count
