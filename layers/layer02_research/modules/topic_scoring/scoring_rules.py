"""
Scoring Rules
Layer 2: Research Engine — Module 8

Defines scoring rules and thresholds:
- Score ranges
- Threshold definitions
- Bonus/penalty rules
- Score interpretation
"""

from typing import Dict, List, Optional


class ScoringRule:
    """A single scoring rule."""

    __slots__ = ("rule_id", "name", "category", "condition",
                 "bonus", "description", "priority")

    def __init__(self, rule_id: str, name: str, category: str = "bonus",
                 condition: str = "", bonus: float = 0.0,
                 description: str = "", priority: int = 1):
        self.rule_id = rule_id
        self.name = name
        self.category = category
        self.condition = condition
        self.bonus = max(-5.0, min(5.0, bonus))
        self.description = description
        self.priority = priority

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id, "name": self.name,
            "category": self.category, "condition": self.condition,
            "bonus": self.bonus, "description": self.description,
            "priority": self.priority,
        }


# Default scoring rules
DEFAULT_RULES = [
    ScoringRule("r1", "High Trend Score", "bonus", "trend_score >= 8.0", 1.5, "Trend is strong"),
    ScoringRule("r2", "Low Competition", "bonus", "competition_score <= 3.0", 1.0, "Low competition is an opportunity"),
    ScoringRule("r3", "High Audience Fit", "bonus", "audience_score >= 7.0", 1.0, "Strong audience match"),
    ScoringRule("r4", "Verified Knowledge", "bonus", "verification_score >= 8.0", 1.5, "Knowledge is verified"),
    ScoringRule("r5", "Declining Trend Penalty", "penalty", "trend_score <= 2.0", -2.0, "Trend is declining"),
    ScoringRule("r6", "Saturated Market Penalty", "penalty", "competition_score >= 9.0", -1.5, "Market is saturated"),
    ScoringRule("r7", "No Knowledge Penalty", "penalty", "knowledge_score <= 1.0", -1.0, "Insufficient knowledge"),
    ScoringRule("r8", "High Confidence Bonus", "bonus", "confidence >= 0.85", 0.5, "High confidence in data"),
]


class ScoringRulesEngine:
    """Manages and applies scoring rules."""

    def __init__(self, rules: Optional[List[ScoringRule]] = None):
        self._rules = {r.rule_id: r for r in (rules or DEFAULT_RULES)}

    def add_rule(self, rule: ScoringRule):
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[ScoringRule]:
        return self._rules.get(rule_id)

    def list_rules(self) -> List[ScoringRule]:
        return sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)

    def evaluate(self, scores: Dict[str, float]) -> List[ScoringRule]:
        """Evaluate which rules apply to the given scores."""
        applied = []
        for rule in self._rules.values():
            try:
                if self._check_condition(rule.condition, scores):
                    applied.append(rule)
            except Exception:
                continue
        return applied

    def compute_bonus(self, scores: Dict[str, float]) -> float:
        """Compute total bonus/penalty from all applicable rules."""
        applied = self.evaluate(scores)
        return round(sum(r.bonus for r in applied), 2)

    def _check_condition(self, condition: str, scores: Dict[str, float]) -> bool:
        """Evaluate a condition string against scores."""
        if not condition:
            return False
        # Replace variable names with values
        expr = condition
        for key, val in scores.items():
            expr = expr.replace(key, str(val))
        # Simple safe evaluation
        return eval(expr)  # noqa: S307

    def reset_to_defaults(self):
        self._rules = {r.rule_id: r for r in DEFAULT_RULES}
