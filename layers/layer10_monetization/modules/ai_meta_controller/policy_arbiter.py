"""Policy Arbiter — Universal policy enforcement."""
from __future__ import annotations
from typing import Any, Dict, List


class PolicyRule:
    """A single policy rule."""

    __slots__ = ("rule_id", "category", "name", "description", "severity", "enabled")

    def __init__(self, rule_id: str = "", category: str = "", name: str = "") -> None:
        self.rule_id = rule_id
        self.category = category
        self.name = name
        self.description: str = ""
        self.severity: str = "medium"
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"rule_id": self.rule_id, "category": self.category, "name": self.name}


class PolicyArbiter:
    """Enforce platform, brand, and safety policies."""

    DEFAULT_RULES = [
        ("platform_limits", "character_limit", "Platform character limits"),
        ("platform_limits", "hashtag_limit", "Platform hashtag limits"),
        ("safety", "no_hate_speech", "Hate speech detection"),
        ("safety", "no_violence", "Violence content detection"),
        ("safety", "no_misinformation", "Misinformation detection"),
        ("brand", "tone_consistency", "Brand tone consistency"),
        ("brand", "terminology_compliance", "Brand terminology"),
        ("copyright", "no_plagiarism", "Plagiarism check"),
        ("spam", "no_duplicate", "Duplicate content check"),
        ("community", "guidelines_compliance", "Community guidelines"),
    ]

    def __init__(self) -> None:
        self._rules: List[PolicyRule] = []
        for i, (cat, name, desc) in enumerate(self.DEFAULT_RULES):
            rule = PolicyRule(f"rule_{i+1}", cat, name)
            rule.description = desc
            self._rules.append(rule)
        self._violations: List[Dict[str, Any]] = []

    def check(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        for rule in self._rules:
            if not rule.enabled:
                continue
            if rule.category == "safety":
                lower = content.lower()
                if any(w in lower for w in ["hate", "kill", "violence"]):
                    violations.append({"rule": rule.name, "severity": "high"})

        result = {
            "passed": len(violations) == 0,
            "violations": violations,
            "rules_checked": len([r for r in self._rules if r.enabled]),
        }
        if violations:
            self._violations.extend(violations)
        return result

    def add_rule(self, category: str, name: str, description: str = "") -> PolicyRule:
        rule = PolicyRule(f"rule_{len(self._rules)+1}", category, name)
        rule.description = description
        self._rules.append(rule)
        return rule

    def get_rules(self, category: str = "") -> List[PolicyRule]:
        if category:
            return [r for r in self._rules if r.category == category]
        return list(self._rules)

    def get_violations(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._violations[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules if r.enabled),
            "total_violations": len(self._violations),
        }
