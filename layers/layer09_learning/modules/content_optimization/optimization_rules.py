"""Optimization Rules — Rule library for improving content."""
from __future__ import annotations
from typing import Any, Dict, List


class OptimizationRule:
    """A single optimization rule."""

    __slots__ = ("rule_id", "rule_type", "description", "target_field",
                 "condition", "action", "priority", "enabled")

    _counter = 0

    def __init__(self, rule_type: str = "general", description: str = "") -> None:
        OptimizationRule._counter += 1
        self.rule_id: str = f"or_{OptimizationRule._counter}"
        self.rule_type = rule_type
        self.description = description
        self.target_field: str = ""
        self.condition: str = ""
        self.action: str = ""
        self.priority: str = "medium"
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "description": self.description,
            "target_field": self.target_field,
            "action": self.action,
            "priority": self.priority,
            "enabled": self.enabled,
        }


class RuleLibrary:
    """Library of optimization rules organized by type."""

    def __init__(self) -> None:
        self._rules: Dict[str, List[OptimizationRule]] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        self.add_rule("title", "Add power words to title", "title", "high")
        self.add_rule("title", "Keep title under 60 characters", "title", "high")
        self.add_rule("hook", "Start with a question or statistic", "opening", "high")
        self.add_rule("body", "Use short paragraphs for readability", "body", "medium")
        self.add_rule("body", "Add bullet points for lists", "body", "medium")
        self.add_rule("body", "Include relevant examples", "body", "medium")
        self.add_rule("cta", "End with a clear call-to-action", "cta", "high")
        self.add_rule("cta", "Use action verbs in CTA", "cta", "medium")
        self.add_rule("seo", "Include primary keyword in first 100 words", "body", "high")
        self.add_rule("seo", "Add 3-5 relevant hashtags", "hashtags", "medium")
        self.add_rule("engagement", "Ask a question to drive comments", "cta", "medium")
        self.add_rule("engagement", "Use emojis strategically", "body", "low")
        self.add_rule("formatting", "Use line breaks between paragraphs", "body", "medium")
        self.add_rule("formatting", "Bold key takeaways", "body", "low")

    def add_rule(self, rule_type: str, description: str,
                 target_field: str = "", priority: str = "medium") -> OptimizationRule:
        rule = OptimizationRule(rule_type, description)
        rule.target_field = target_field
        rule.priority = priority
        self._rules.setdefault(rule_type, []).append(rule)
        return rule

    def get_rules(self, rule_type: str = "") -> List[OptimizationRule]:
        if rule_type:
            return [r for r in self._rules.get(rule_type, []) if r.enabled]
        return [r for rules in self._rules.values() for r in rules if r.enabled]

    def get_by_field(self, target_field: str) -> List[OptimizationRule]:
        return [r for rules in self._rules.values()
                for r in rules if r.target_field == target_field and r.enabled]

    def get_by_priority(self, priority: str) -> List[OptimizationRule]:
        return [r for rules in self._rules.values()
                for r in rules if r.priority == priority and r.enabled]

    @property
    def rule_count(self) -> int:
        return sum(len(rules) for rules in self._rules.values())
