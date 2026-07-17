"""Content Safety — Platform-specific content safety policies."""
from __future__ import annotations
from typing import Any, Dict, List


class SafetyRule:
    """A single content safety rule."""

    __slots__ = ("rule_id", "category", "severity", "description",
                 "blocked_terms", "enabled")

    def __init__(self, rule_id: str = "", category: str = "", severity: str = "medium") -> None:
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.description: str = ""
        self.blocked_terms: List[str] = []
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "enabled": self.enabled,
        }


class ContentSafety:
    """Content safety policies across all platforms."""

    def __init__(self) -> None:
        self._rules: List[SafetyRule] = self._default_rules()

    def _default_rules(self) -> List[SafetyRule]:
        return [
            SafetyRule("safe_1", "hate_speech", "critical"),
            SafetyRule("safe_2", "violence", "critical"),
            SafetyRule("safe_3", "spam", "high"),
            SafetyRule("safe_4", "misinformation", "high"),
            SafetyRule("safe_5", "adult_content", "high"),
            SafetyRule("safe_6", "harassment", "high"),
        ]

    def check_content(self, content: str) -> List[SafetyRule]:
        violations: List[SafetyRule] = []
        content_lower = content.lower()
        for rule in self._rules:
            if not rule.enabled:
                continue
            for term in rule.blocked_terms:
                if term.lower() in content_lower:
                    violations.append(rule)
                    break
        return violations

    def add_rule(self, rule: SafetyRule) -> None:
        self._rules.append(rule)

    def get_rules(self) -> List[SafetyRule]:
        return list(self._rules)

    def get_rules_by_category(self, category: str) -> List[SafetyRule]:
        return [r for r in self._rules if r.category == category]

    def is_safe(self, content: str) -> bool:
        return len(self.check_content(content)) == 0

    def get_violation_count(self, content: str) -> int:
        return len(self.check_content(content))
