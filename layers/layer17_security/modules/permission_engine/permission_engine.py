"""PermissionEngine — fine-grained permission evaluation."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Set


class PermissionRule:
    __slots__ = ("resource", "action", "effect", "conditions")

    def __init__(self, resource: str, action: str, effect: str = "allow",
                 conditions: Optional[Dict[str, Any]] = None) -> None:
        self.resource = resource
        self.action = action
        self.effect = effect
        self.conditions = conditions or {}


class PermissionEngine:
    def __init__(self) -> None:
        self._rules: List[PermissionRule] = []
        self._role_permissions: Dict[str, Set[str]] = {}

    def add_rule(self, resource: str, action: str, effect: str = "allow",
                 conditions: Optional[Dict[str, Any]] = None) -> PermissionRule:
        rule = PermissionRule(resource, action, effect, conditions)
        self._rules.append(rule)
        return rule

    def check_permission(self, resource: str, action: str,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        for rule in self._rules:
            if rule.resource == resource and rule.action == action:
                if rule.conditions and context:
                    met = all(context.get(k) == v for k, v in rule.conditions.items())
                    if not met:
                        continue
                return {"allowed": rule.effect == "allow", "rule": rule.resource}
        return {"allowed": False, "rule": "no_matching_rule"}

    def assign_role_permissions(self, role: str, permissions: List[str]) -> None:
        self._role_permissions[role] = set(permissions)

    def check_role_permission(self, role: str, permission: str) -> bool:
        return permission in self._role_permissions.get(role, set())

    def list_rules(self) -> List[Dict[str, Any]]:
        return [{"resource": r.resource, "action": r.action, "effect": r.effect} for r in self._rules]

    def count(self) -> int:
        return len(self._rules)
