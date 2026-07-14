"""Rule Engine — IF/THEN rule evaluation for content decisions."""

from typing import Any, Callable, Dict, List


class Rule:
    def __init__(self, name: str, condition: Callable[[Dict], bool], action: Callable[[Dict], Any], priority: int = 0):
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority
        self.trigger_count = 0


class RuleEngine:
    def __init__(self):
        self._rules: List[Rule] = []

    def add_rule(self, name: str, condition: Callable, action: Callable, priority: int = 0):
        self._rules.append(Rule(name, condition, action, priority))
        self._rules.sort(key=lambda r: -r.priority)

    def evaluate(self, context: Dict) -> List[Dict]:
        results = []
        for rule in self._rules:
            try:
                if rule.condition(context):
                    result = rule.action(context)
                    rule.trigger_count += 1
                    results.append({"rule": rule.name, "result": result, "triggered": True})
            except Exception:
                results.append({"rule": rule.name, "result": None, "triggered": False})
        return results

    def get_triggered_rules(self) -> List[str]:
        return [r.name for r in self._rules if r.trigger_count > 0]

    def reset_counts(self):
        for r in self._rules:
            r.trigger_count = 0
