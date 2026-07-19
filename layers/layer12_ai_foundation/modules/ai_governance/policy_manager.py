"""PolicyManager — manage governance policies."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .models import Policy, PolicyType

class PolicyManager:
    def __init__(self) -> None:
        self._policies: Dict[str, Policy] = {}
    def add(self, policy: Policy) -> None:
        self._policies[policy.policy_id] = policy
    def get(self, policy_id: str) -> Optional[Policy]:
        return self._policies.get(policy_id)
    def remove(self, policy_id: str) -> bool:
        return self._policies.pop(policy_id, None) is not None
    def list_active(self) -> List[Policy]:
        return [p for p in self._policies.values() if p.active]
    def list_by_type(self, policy_type: PolicyType) -> List[Policy]:
        return [p for p in self._policies.values() if p.policy_type == policy_type]
    def count(self) -> int:
        return len(self._policies)
    def to_dict(self) -> Dict[str, Any]:
        return {pid: p.to_dict() for pid, p in self._policies.items()}
