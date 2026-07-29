"""RuleEngine — Evaluate automation rules with IF-THEN logic."""
from __future__ import annotations
import time
import re
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import (
    Rule, RuleAction,
)
from layers.layer23_website_manager.automation_engine.exceptions import RuleEngineError


class RuleEngine:
    """Evaluate rules and execute actions."""

    def __init__(self) -> None:
        self._rules: Dict[str, Rule] = {}
        self._action_handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()

    def add_rule(self, name: str, condition_expr: str,
                 actions: Optional[List[RuleAction]] = None,
                 priority: int = 100) -> Rule:
        rule = Rule(name=name, condition_expr=condition_expr,
                    actions=actions or [], priority=priority)
        with self._lock:
            self._rules[rule.rule_id] = rule
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        with self._lock:
            return self._rules.pop(rule_id, None) is not None

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[Rule]:
        return list(self._rules.values())

    def enable_rule(self, rule_id: str) -> bool:
        r = self._rules.get(rule_id)
        if not r:
            return False
        r.enabled = True
        return True

    def disable_rule(self, rule_id: str) -> bool:
        r = self._rules.get(rule_id)
        if not r:
            return False
        r.enabled = False
        return True

    def register_action(self, action_type: str, handler: Callable) -> None:
        with self._lock:
            self._action_handlers[action_type] = handler

    def evaluate_condition(self, condition_expr: str,
                           context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition expression against context values."""
        # Support: key > value, key < value, key == value, key >= value, key <= value
        pattern = r'^([\w_]+)\s*(>|<|>=|<=|==|!=)\s*([\w_.-]+)$'
        match = re.match(pattern, condition_expr.strip())
        if not match:
            return False
        key, op, val_str = match.groups()
        actual = context.get(key)
        if actual is None:
            return False
        try:
            val = float(val_str) if '.' in val_str or val_str.isdigit() else val_str
        except ValueError:
            val = val_str
        if op == '>': return actual > val
        elif op == '<': return actual < val
        elif op == '>=': return actual >= val
        elif op == '<=': return actual <= val
        elif op == '==': return actual == val
        elif op == '!=': return actual != val
        return False

    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> bool:
        if not rule.enabled:
            return False
        if not self.evaluate_condition(rule.condition_expr, context):
            return False
        rule.trigger_count += 1
        rule.last_triggered = time.time()
        for action in rule.actions:
            handler = self._action_handlers.get(action.action_type)
            if handler:
                try:
                    handler(action, context)
                except Exception:
                    pass
        return True

    def evaluate_all(self, context: Dict[str, Any]) -> List[str]:
        triggered = []
        sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority)
        for rule in sorted_rules:
            if self.evaluate_rule(rule, context):
                triggered.append(rule.rule_id)
        return triggered

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_rules": len(self._rules),
                "enabled": sum(1 for r in self._rules.values() if r.enabled),
                "total_triggers": sum(r.trigger_count for r in self._rules.values()),
                "handlers": len(self._action_handlers),
            }
