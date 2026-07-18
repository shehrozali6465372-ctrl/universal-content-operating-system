"""lifecycle_manager.py — Object lifecycle management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class LifecycleRule:
    """Lifecycle rule for object management."""
    __slots__ = ("rule_id", "prefix", "transition_days", "expiration_days",
                 "storage_class", "enabled")
    _counter = 0

    def __init__(self, prefix: str = "", transition_days: int = 0,
                 expiration_days: int = 0, storage_class: str = "standard") -> None:
        LifecycleRule._counter += 1
        self.rule_id: int = LifecycleRule._counter
        self.prefix = prefix
        self.transition_days = transition_days
        self.expiration_days = expiration_days
        self.storage_class = storage_class
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"rule_id": self.rule_id, "prefix": self.prefix,
                "transition_days": self.transition_days,
                "expiration_days": self.expiration_days}


class LifecycleManager:
    """Manages object lifecycle rules."""

    def __init__(self) -> None:
        self._rules: Dict[int, LifecycleRule] = {}

    def add_rule(self, rule: LifecycleRule) -> None:
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: int) -> bool:
        return self._rules.pop(rule_id, None) is not None

    def get_rules(self) -> List[LifecycleRule]:
        return list(self._rules.values())

    def evaluate(self, object_key: str, age_days: int) -> Optional[str]:
        for rule in self._rules.values():
            if rule.enabled and object_key.startswith(rule.prefix):
                if rule.expiration_days > 0 and age_days >= rule.expiration_days:
                    return "expired"
                if rule.transition_days > 0 and age_days >= rule.transition_days:
                    return rule.storage_class
        return None

    def count(self) -> int:
        return len(self._rules)
