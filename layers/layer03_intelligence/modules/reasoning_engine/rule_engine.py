"""Rule Engine - Evaluates IF-THEN rules for decision making."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional


class Rule:
    """A single IF-THEN rule."""
    __slots__ = ("name", "condition", "action", "priority", "enabled", "tags")

    def __init__(self, name: str, condition: Callable[[Dict], bool],
                 action: Callable[[Dict], Any], priority: int = 0,
                 tags: Optional[List[str]] = None):
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority
        self.enabled = True
        self.tags = tags or []

    def evaluate(self, context: Dict) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            if self.condition(context):
                return self.action(context)
        except Exception:
            pass
        return None

    def to_dict(self) -> Dict:
        return {"name": self.name, "priority": self.priority,
                "enabled": self.enabled, "tags": list(self.tags)}


class RuleResult:
    """Result of rule evaluation."""
    __slots__ = ("rules_fired", "results", "total_rules", "execution_time")

    def __init__(self) -> None:
        self.rules_fired: List[str] = []
        self.results: Dict[str, Any] = {}
        self.total_rules = 0
        self.execution_time = 0.0

    def to_dict(self) -> Dict:
        return {"rules_fired": list(self.rules_fired), "results": dict(self.results),
                "total_rules": self.total_rules, "execution_time": round(self.execution_time, 4)}


class RuleEngine:
    """Evaluates a set of rules against a context."""

    def __init__(self) -> None:
        self._rules: List[Rule] = []

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def add_simple_rule(self, name: str, condition_fn: Callable, action_fn: Callable,
                        priority: int = 0, tags: Optional[List[str]] = None) -> None:
        self.add_rule(Rule(name, condition_fn, action_fn, priority, tags))

    def evaluate(self, context: Dict) -> RuleResult:
        import time
        result = RuleResult()
        start = time.perf_counter()
        result.total_rules = len(self._rules)

        for rule in self._rules:
            fired = rule.evaluate(context)
            if fired is not None:
                result.rules_fired.append(rule.name)
                result.results[rule.name] = fired

        result.execution_time = time.perf_counter() - start
        return result

    def evaluate_first_match(self, context: Dict) -> Optional[Any]:
        for rule in self._rules:
            if not rule.enabled:
                continue
            try:
                if rule.condition(context):
                    return rule.action(context)
            except Exception:
                continue
        return None

    def get_rules_by_tag(self, tag: str) -> List[Rule]:
        return [r for r in self._rules if tag in r.tags]

    def enable_rule(self, name: str) -> None:
        for r in self._rules:
            if r.name == name:
                r.enabled = True

    def disable_rule(self, name: str) -> None:
        for r in self._rules:
            if r.name == name:
                r.enabled = False

    def count(self) -> int:
        return len(self._rules)

    def to_dict(self) -> Dict:
        return {"rules": [r.to_dict() for r in self._rules], "count": self.count()}
