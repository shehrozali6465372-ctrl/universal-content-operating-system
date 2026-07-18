"""lifecycle_policy.py — Object lifecycle policies."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class LifecyclePolicy:
    """Object lifecycle policy."""
    __slots__ = ("name", "prefix", "transition_days", "expiration_days",
                 "storage_class", "enabled")
    _counter = 0

    def __init__(self, name: str = "", prefix: str = "") -> None:
        LifecyclePolicy._counter += 1
        self.name = name or f"policy_{LifecyclePolicy._counter}"
        self.prefix = prefix
        self.transition_days: int = 0
        self.expiration_days: int = 0
        self.storage_class: str = "standard"
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "prefix": self.prefix,
                "transition_days": self.transition_days, "enabled": self.enabled}


class LifecyclePolicyManager:
    """Manages lifecycle policies."""

    def __init__(self) -> None:
        self._policies: Dict[str, LifecyclePolicy] = {}

    def add(self, policy: LifecyclePolicy) -> None:
        self._policies[policy.name] = policy

    def remove(self, name: str) -> bool:
        return self._policies.pop(name, None) is not None

    def evaluate(self, object_key: str, age_days: int) -> Optional[str]:
        for policy in self._policies.values():
            if policy.enabled and object_key.startswith(policy.prefix):
                if policy.expiration_days > 0 and age_days >= policy.expiration_days:
                    return "expired"
                if policy.transition_days > 0 and age_days >= policy.transition_days:
                    return policy.storage_class
        return None

    def list_all(self) -> List[LifecyclePolicy]:
        return list(self._policies.values())
