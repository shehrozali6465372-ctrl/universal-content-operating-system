"""SecurityPolicies — define and enforce security policies."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class PolicyLevel(str, Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"


class SecurityPolicy:
    __slots__ = ("policy_id", "name", "level", "rules", "active",
                 "created_at", "metadata")

    def __init__(self, name: str, level: PolicyLevel = PolicyLevel.MEDIUM) -> None:
        self.policy_id = f"pol_{name}"
        self.name = name
        self.level = level
        self.rules: List[Dict[str, Any]] = []
        self.active = True
        self.created_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def add_rule(self, rule_name: str, check_fn: Callable, description: str = "") -> None:
        self.rules.append({"name": rule_name, "check": check_fn, "description": description})

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        for rule in self.rules:
            try:
                if not rule["check"](context):
                    violations.append(rule["name"])
            except Exception:
                violations.append(rule["name"])
        return {"passed": len(violations) == 0, "violations": violations}

    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "name": self.name,
                "level": self.level.value, "active": self.active,
                "rules_count": len(self.rules)}


class SecurityPolicies:
    def __init__(self) -> None:
        self._policies: Dict[str, SecurityPolicy] = {}
        self._history: List[Dict[str, Any]] = []

    def create_policy(self, name: str, level: PolicyLevel = PolicyLevel.MEDIUM) -> SecurityPolicy:
        policy = SecurityPolicy(name, level)
        self._policies[policy.policy_id] = policy
        return policy

    def evaluate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for pid, policy in self._policies.items():
            if policy.active:
                results[pid] = policy.evaluate(context)
        all_passed = all(r["passed"] for r in results.values())
        self._history.append({"all_passed": all_passed, "time": time.time()})
        return {"all_passed": all_passed, "policies": results}

    def get_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        return self._policies.get(policy_id)

    def list_policies(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._policies.values()]

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def count(self) -> int:
        return len(self._policies)
