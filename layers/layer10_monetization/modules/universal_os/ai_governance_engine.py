"""AIGovernanceEngine — deterministic policy evaluation with auditable violations."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AGX_COUNTER = itertools.count(1)
POLICY_TYPES = ("ethics", "safety", "brand", "legal", "platform", "internal")
SEVERITIES = ("info", "warning", "error", "critical")


class Policy:
    def __init__(self, policy_type: str, name: str) -> None:
        self.policy_id = f"pol_{next(_AGX_COUNTER)}"
        self.policy_type = policy_type if policy_type in POLICY_TYPES else "internal"
        self.name = name
        self.rules: List[str] = []
        self.enforced = True
        self.severity = "warning"
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "type": self.policy_type,
                "name": self.name, "enforced": self.enforced,
                "severity": self.severity, "rule_count": len(self.rules)}


class AIGovernanceEngine:
    """Evaluate registered no_* rules and retain auditable violation metadata."""

    def __init__(self) -> None:
        self._policies: List[Policy] = []
        self._violations: List[Dict[str, Any]] = []

    def add_policy(self, policy_type: str, name: str,
                   rules: Optional[List[str]] = None,
                   severity: str = "warning") -> Policy:
        if severity not in SEVERITIES:
            raise ValueError("invalid severity")
        policy = Policy(policy_type, name)
        policy.rules = list(rules or [])
        policy.severity = severity
        self._policies.append(policy)
        return policy

    def evaluate(self, content: Dict[str, Any],
                 policy_type: str = "") -> Dict[str, Any]:
        policies = self._policies if not policy_type else [
            p for p in self._policies if p.policy_type == policy_type
        ]
        results: List[Dict[str, Any]] = []
        haystack = str(content).lower()
        for policy in policies:
            if not policy.enforced:
                continue
            failed_rules: List[str] = []
            for rule in policy.rules:
                if rule.startswith("no_") and rule[3:].lower() in haystack:
                    failed_rules.append(rule)
                    self._violations.append({
                        "policy_id": policy.policy_id, "policy": policy.name,
                        "policy_type": policy.policy_type, "rule": rule,
                        "severity": policy.severity, "timestamp": time.time(),
                    })
            results.append({"policy": policy.name, "passed": not failed_rules,
                            "failed_rules": failed_rules})
        passed = sum(1 for result in results if result["passed"])
        return {"total_policies": len(results), "passed": passed,
                "failed": len(results) - passed, "details": results}

    def get_policies(self, policy_type: str = "") -> List[Policy]:
        return [p for p in self._policies
                if not policy_type or p.policy_type == policy_type]

    def get_violations(self, policy_type: str = "") -> List[Dict[str, Any]]:
        return [v for v in self._violations
                if not policy_type or v["policy_type"] == policy_type]

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for policy in self._policies:
            types[policy.policy_type] = types.get(policy.policy_type, 0) + 1
        return {"total_policies": len(self._policies),
                "total_violations": len(self._violations), "by_type": types}
