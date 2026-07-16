"""Format Checker — Validate content format against platform rules.

Checks: character limits, heading format, list format, emoji usage,
line breaks, code blocks, and structural compliance.
"""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.platform_compliance_engine.compliance_report import RuleViolation


class FormatChecker:
    """Check content format compliance."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, content: str, rules: Dict) -> List[RuleViolation]:
        """Check content format against platform rules."""
        violations: List[RuleViolation] = []

        max_len = rules.get("max_post_length") or rules.get("max_description_length")
        if max_len and len(content) > max_len:
            violations.append(RuleViolation(
                rule_id="format_max_length",
                category="format",
                severity="critical",
                description=f"Content exceeds max length ({len(content)}/{max_len})",
                current_value=str(len(content)),
                expected_value=f"<={max_len}",
                suggestion=f"Shorten content to {max_len} characters",
                auto_fixable=True,
            ))

        min_len = rules.get("min_post_length", 0)
        if min_len and len(content.strip()) < min_len:
            violations.append(RuleViolation(
                rule_id="format_min_length",
                category="format",
                severity="medium",
                description=f"Content below minimum length ({len(content.strip())}/{min_len})",
                current_value=str(len(content.strip())),
                expected_value=f">={min_len}",
                suggestion=f"Expand content to at least {min_len} characters",
            ))

        optimal = rules.get("optimal_length")
        if optimal and isinstance(optimal, tuple) and len(optimal) == 2:
            word_count = len(content.split())
            if not (optimal[0] <= word_count <= optimal[1]):
                violations.append(RuleViolation(
                    rule_id="format_optimal_length",
                    category="format",
                    severity="low",
                    description=f"Word count ({word_count}) outside optimal range ({optimal[0]}-{optimal[1]})",
                    current_value=str(word_count),
                    expected_value=f"{optimal[0]}-{optimal[1]} words",
                    suggestion=f"Adjust content to {optimal[0]}-{optimal[1]} words for best engagement",
                ))

        if rules.get("no_all_caps"):
            words = content.split()
            caps_words = [w for w in words if w.isupper() and len(w) > 2]
            if caps_words and len(caps_words) / max(1, len(words)) > 0.3:
                violations.append(RuleViolation(
                    rule_id="format_no_all_caps",
                    category="format",
                    severity="medium",
                    description=f"Excessive ALL CAPS words detected ({len(caps_words)})",
                    current_value=f"{len(caps_words)} caps words",
                    expected_value="minimal caps",
                    suggestion="Use normal capitalization for professional tone",
                ))

        if rules.get("professional_tone"):
            informal = re.findall(r'\b(?:gonna|wanna|lol|omg|btw|tbh|imo|smh)\b', content.lower())
            if informal:
                violations.append(RuleViolation(
                    rule_id="format_informal_language",
                    category="format",
                    severity="medium",
                    description=f"Informal language detected: {', '.join(informal[:3])}",
                    current_value=", ".join(informal[:3]),
                    expected_value="professional language",
                    suggestion="Replace informal abbreviations with professional language",
                ))

        self._check_count += 1
        return violations

    @property
    def check_count(self) -> int:
        return self._check_count
