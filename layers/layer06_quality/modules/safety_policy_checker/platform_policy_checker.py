"""Platform Policy Checker — Validate content against platform-specific rules.

Covers: Facebook, Instagram, X/Twitter, LinkedIn, TikTok, YouTube, Pinterest, Reddit, Medium.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List

from layers.layer06_quality.modules.safety_policy_checker.safety_report import PolicyCheckResult, SafetyFlag


PLATFORM_POLICIES: Dict[str, Dict[str, Any]] = {
    "facebook": {
        "max_length": 63206,
        "max_hashtags": 30,
        "max_mentions": 5,
        "rules": {
            "no_engagement_bait": True,
            "no_violence": True,
            "no_hate_speech": True,
            "no_misinformation": True,
            "no_spam": True,
        },
        "warnings": ["avoid_link_in_first_comment", "image_text_ratio"],
    },
    "instagram": {
        "max_length": 2200,
        "max_hashtags": 30,
        "max_mentions": 5,
        "rules": {
            "no_visual_nudity": True,
            "no_violence": True,
            "no_hate_speech": True,
            "no_misinformation": True,
        },
        "warnings": ["avoid_hashtag_stuffing", "use_3_to_5_hashtags"],
    },
    "twitter": {
        "max_length": 280,
        "max_hashtags": 5,
        "max_mentions": 5,
        "rules": {
            "no_spam": True,
            "no_hate_speech": True,
            "no_violence": True,
        },
        "warnings": ["avoid_too_many_hashtags", "keep_concise"],
    },
    "linkedin": {
        "max_length": 3000,
        "max_hashtags": 5,
        "max_mentions": 5,
        "rules": {
            "professional_tone": True,
            "no_spam": True,
            "no_hate_speech": True,
        },
        "warnings": ["use_professional_language", "no_all_caps"],
    },
    "tiktok": {
        "max_length": 2200,
        "max_hashtags": 5,
        "max_mentions": 5,
        "rules": {
            "no_violence": True,
            "no_hate_speech": True,
            "no_misinformation": True,
        },
        "warnings": ["use_trending_hashtags", "keep_short"],
    },
    "youtube": {
        "max_length": 5000,
        "max_hashtags": 15,
        "max_mentions": 5,
        "rules": {
            "no_violence": True,
            "no_hate_speech": True,
            "no_misinformation": True,
            "no_spam": True,
        },
        "warnings": ["use_descriptive_title", "add_timestamps"],
    },
    "pinterest": {
        "max_length": 500,
        "max_hashtags": 20,
        "max_mentions": 0,
        "rules": {
            "no_spam": True,
            "no_hate_speech": True,
        },
        "warnings": ["use_keyword_rich_description", "vertical_images_preferred"],
    },
    "reddit": {
        "max_length": 40000,
        "max_hashtags": 0,
        "max_mentions": 0,
        "rules": {
            "no_spam": True,
            "no_self_promotion_excessive": True,
            "no_hate_speech": True,
        },
        "warnings": ["follow_subreddit_rules", "provide_value_first"],
    },
    "medium": {
        "max_length": 100000,
        "max_hashtags": 0,
        "max_mentions": 0,
        "rules": {
            "no_plagiarism": True,
            "no_spam": True,
            "original_content": True,
        },
        "warnings": ["use_claps_for_engagement", "add_images"],
    },
}


class PlatformPolicyChecker:
    """Check content against platform-specific policies."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, content: str, platform: str) -> PolicyCheckResult:
        """Check content against a specific platform's policy."""
        platform_lower = platform.lower().strip()
        result = PolicyCheckResult(platform=platform_lower)

        policy = PLATFORM_POLICIES.get(platform_lower)
        if not policy:
            result.issues.append(f"unknown_platform: {platform}")
            result.score = 0.5
            return result

        self._check_length(content, policy, result)
        self._check_hashtags(content, policy, result)
        self._check_mentions(content, policy, result)
        self._check_caps(content, result)

        if not result.flags:
            result.score = 1.0
        result.is_compliant = not any(f.severity in ("critical", "high") for f in result.flags)

        self._check_count += 1
        return result

    def check_batch(
        self, content: str, platforms: List[str],
    ) -> List[PolicyCheckResult]:
        """Check content against multiple platforms."""
        return [self.check(content, p) for p in platforms]

    def check_all_platforms(self, content: str) -> List[PolicyCheckResult]:
        """Check content against all known platforms."""
        return self.check_batch(content, list(PLATFORM_POLICIES.keys()))

    def get_compliant_platforms(self, results: List[PolicyCheckResult]) -> List[str]:
        """Return platforms where content is compliant."""
        return [r.platform for r in results if r.is_compliant]

    def _check_length(self, content: str, policy: Dict, result: PolicyCheckResult) -> None:
        max_len = policy.get("max_length", 100000)
        if len(content) > max_len:
            result.flags.append(SafetyFlag(
                category="platform", subcategory="length_exceeded",
                severity="high", confidence=0.95,
                matched_text=f"Content length {len(content)} exceeds {max_len}",
                description=f"Content exceeds {result.platform} character limit ({max_len})",
                suggestion=f"Shorten content to under {max_len} characters",
            ))

    def _check_hashtags(self, content: str, policy: Dict, result: PolicyCheckResult) -> None:
        max_tags = policy.get("max_hashtags", 0)
        if max_tags == 0:
            hashtags = re.findall(r'#\w+', content)
            if hashtags:
                result.flags.append(SafetyFlag(
                    category="platform", subcategory="hashtags_not_allowed",
                    severity="medium", confidence=0.8,
                    matched_text=f"{len(hashtags)} hashtag(s) found",
                    description=f"{result.platform} does not support hashtags",
                    suggestion="Remove hashtags for this platform",
                ))
            return
        hashtags = re.findall(r'#\w+', content)
        if len(hashtags) > max_tags:
            result.flags.append(SafetyFlag(
                category="platform", subcategory="too_many_hashtags",
                severity="medium", confidence=0.85,
                matched_text=f"{len(hashtags)} hashtags (max {max_tags})",
                description=f"Too many hashtags for {result.platform} (max {max_tags})",
                suggestion=f"Reduce hashtags to {max_tags} or fewer",
            ))

    def _check_mentions(self, content: str, policy: Dict, result: PolicyCheckResult) -> None:
        max_mentions = policy.get("max_mentions", 0)
        if max_mentions == 0:
            mentions = re.findall(r'@\w+', content)
            if mentions:
                result.flags.append(SafetyFlag(
                    category="platform", subcategory="mentions_not_allowed",
                    severity="low", confidence=0.6,
                    matched_text=f"{len(mentions)} mention(s) found",
                    description=f"{result.platform} does not support @mentions",
                    suggestion="Remove @mentions for this platform",
                ))
            return
        mentions = re.findall(r'@\w+', content)
        if len(mentions) > max_mentions:
            result.flags.append(SafetyFlag(
                category="platform", subcategory="too_many_mentions",
                severity="low", confidence=0.7,
                matched_text=f"{len(mentions)} mentions (max {max_mentions})",
                description=f"Too many mentions for {result.platform} (max {max_mentions})",
                suggestion=f"Reduce mentions to {max_mentions} or fewer",
            ))

    def _check_caps(self, content: str, result: PolicyCheckResult) -> None:
        words = content.split()
        if len(words) < 5:
            return
        caps = sum(1 for w in words if w.isupper() and len(w) > 1)
        if caps / len(words) > 0.5:
            result.flags.append(SafetyFlag(
                category="platform", subcategory="excessive_caps",
                severity="low", confidence=0.6,
                matched_text=f"{caps} of {len(words)} words ALL CAPS",
                description="Excessive ALL CAPS may violate platform guidelines",
                suggestion="Use normal capitalization",
            ))

    @property
    def check_count(self) -> int:
        return self._check_count
