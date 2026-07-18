"""AIGovernanceEngine — Ethics, policies, safety, brand rules enforcement."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AGX_COUNTER = itertools.count(1)

POLICY_TYPES = ("ethics", "safety", "brand", "legal", "platform", "internal")


class Policy:
    """A governance policy."""

    __slots__ = ("policy_id", "policy_type", "name", "rules",
                 "enforced", "severity", "created_at")

    def __init__(self, policy_type: str = "", name: str = "") -> None:
        self.policy_id: str = f"pol_{next(_AGX_COUNTER)}"
        self.policy_type = policy_type if policy_type in POLICY_TYPES else "internal"
        self.name = name
        self.rules: List[str] = []
        self.enforced: bool = True
        self.severity: str = "warning"
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "type": self.policy_type,
                "name": self.name, "enforced": self.enforced,
                "rule_count": len(self.rules)}


class AIGovernanceEngine:
    """Enforce ethics, safety, brand, legal, and platform policies."""

    def __init__(self) -> None:
        self._policies: List[Policy] = []
        self._violations: List[Dict[str, Any]] = []

    def add_policy(self, policy_type: str, name: str,
                   rules: Optional[List[str]] = None,
                   severity: str = "warning") -> Policy:
        policy = Policy(policy_type, name)
        if rules:
            policy.rules = list(rules)
        policy.severity = severity
        self._policies.append(policy)
        return policy

    def evaluate(self, content: Dict[str, Any],
                 policy_type: str = "") -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        policies = self._policies
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        for policy in policies:
            if policy.enforced:
                passed = True
                for rule in policy.rules:
                    if rule.startswith("no_") and rule[3:] in str(content):
                        passed = False
                        self._violations.append({"policy": policy.name,
                                                  "rule": rule,
                                                  "timestamp": time.time()})
                results.append({"policy": policy.name, "passed": passed})
        total = len(results)
        passed_count = sum(1 for r in results if r["passed"])
        return {"total_policies": total, "passed": passed_count,
                "failed": total - passed_count, "details": results}

    def get_policies(self, policy_type: str = "") -> List[Policy]:
        if policy_type:
            return [p for p in self._policies if p.policy_type == policy_type]
        return list(self._policies)

    def get_violations(self, policy_type: str = "") -> List[Dict[str, Any]]:
        if policy_type:
            return [v for v in self._violations
                    if v.get("policy_type") == policy_type]
        return list(self._violations)

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for p in self._policies:
            types[p.policy_type] = types.get(p.policy_type, 0) + 1
        return {"total_policies": len(self._policies),
                "total_violations": len(self._violations),
                "by_type": types}
