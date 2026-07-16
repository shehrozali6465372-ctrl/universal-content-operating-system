"""Content Policy Checker — Validate content against platform content policies.

Checks: forbidden patterns, engagement bait, spam signals,
link limits, mention limits, hashtag limits.
"""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.platform_compliance_engine.compliance_report import RuleViolation


class ContentPolicyChecker:
    """Check content against platform-specific policies."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, content: str, rules: Dict) -> List[RuleViolation]:
        """Check content against platform policies."""
        violations: List[RuleViolation] = []
        content_lower = content.lower()

        # Forbidden patterns
        forbidden = rules.get("forbidden_patterns", [])
        for pattern in forbidden:
            match = re.search(pattern, content_lower)
            if match:
                violations.append(RuleViolation(
                    rule_id="policy_forbidden_pattern",
                    category="policy",
                    severity="high",
                    description=f"Forbidden pattern detected: '{match.group()}'",
                    current_value=match.group(),
                    expected_value="no forbidden content",
                    suggestion="Remove or rephrase the flagged content",
                ))

        # Engagement bait
        if rules.get("no_engagement_bait"):
            bait = re.findall(
                r'\b(?:like\s+and\s+share|tag\s+a\s+friend|share\s+if|comment\s+below|'
                r'tell\s+us\s+what\s+you\s+think|do\s+you\s+agree)\b',
                content_lower,
            )
            if bait:
                violations.append(RuleViolation(
                    rule_id="policy_engagement_bait",
                    category="policy",
                    severity="high",
                    description=f"Engagement bait detected: {', '.join(bait[:3])}",
                    current_value=", ".join(bait[:3]),
                    expected_value="organic engagement",
                    suggestion="Replace engagement bait with genuine calls to action",
                ))

        # Hashtag limits
        hashtags = re.findall(r'#\w+', content)
        max_tags = rules.get("max_hashtags")
        if max_tags and len(hashtags) > max_tags:
            violations.append(RuleViolation(
                rule_id="policy_hashtag_limit",
                category="policy",
                severity="high",
                description=f"Too many hashtags ({len(hashtags)}/{max_tags})",
                current_value=str(len(hashtags)),
                expected_value=f"<={max_tags}",
                suggestion=f"Reduce hashtags to {max_tags} or fewer",
                auto_fixable=True,
            ))

        # Mention limits
        mentions = re.findall(r'@\w+', content)
        max_mentions = rules.get("max_mentions", 5)
        if len(mentions) > max_mentions:
            violations.append(RuleViolation(
                rule_id="policy_mention_limit",
                category="policy",
                severity="medium",
                description=f"Too many mentions ({len(mentions)}/{max_mentions})",
                current_value=str(len(mentions)),
                expected_value=f"<={max_mentions}",
                suggestion=f"Reduce mentions to {max_mentions} or fewer",
                auto_fixable=True,
            ))

        # Link limits
        links = re.findall(r'https?://\S+', content)
        max_links = rules.get("max_link_preview", 999)
        if len(links) > max_links:
            violations.append(RuleViolation(
                rule_id="policy_link_limit",
                category="policy",
                severity="medium",
                description=f"Too many links ({len(links)}/{max_links})",
                current_value=str(len(links)),
                expected_value=f"<={max_links}",
                suggestion=f"Reduce links to {max_links} or fewer",
                auto_fixable=True,
            ))

        # Required hashtags
        if rules.get("requires_hashtags") and not hashtags:
            violations.append(RuleViolation(
                rule_id="policy_requires_hashtags",
                category="policy",
                severity="medium",
                description="Platform requires hashtags but none found",
                current_value="0",
                expected_value=">=1",
                suggestion="Add at least 3-5 relevant hashtags",
            ))

        self._check_count += 1
        return violations

    @property
    def check_count(self) -> int:
        return self._check_count
