"""FeatureFlagManager — Enable/disable experimental features, beta models, A/B tests."""
from __future__ import annotations
from typing import Any, Dict, List


class FeatureFlag:
    """A feature flag."""

    __slots__ = ("name", "enabled", "description", "rollout_percentage", "metadata")

    def __init__(self, name: str = "", enabled: bool = False) -> None:
        self.name = name
        self.enabled = enabled
        self.description: str = ""
        self.rollout_percentage: float = 100.0 if enabled else 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "enabled": self.enabled,
                "rollout_percentage": self.rollout_percentage,
                "description": self.description}


class FeatureFlagManager:
    """Manage experimental features, beta models, and A/B tests."""

    def __init__(self) -> None:
        self._flags: Dict[str, FeatureFlag] = {}

    def create(self, name: str, enabled: bool = False,
               description: str = "",
               rollout_percentage: float = 100.0) -> FeatureFlag:
        if name in self._flags:
            return self._flags[name]
        flag = FeatureFlag(name, enabled)
        flag.description = description
        flag.rollout_percentage = rollout_percentage if enabled else 0.0
        self._flags[name] = flag
        return flag

    def enable(self, name: str) -> bool:
        flag = self._flags.get(name)
        if flag:
            flag.enabled = True
            flag.rollout_percentage = 100.0
            return True
        return False

    def disable(self, name: str) -> bool:
        flag = self._flags.get(name)
        if flag:
            flag.enabled = False
            flag.rollout_percentage = 0.0
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        flag = self._flags.get(name)
        return flag is not None and flag.enabled

    def set_rollout(self, name: str, percentage: float) -> bool:
        flag = self._flags.get(name)
        if flag:
            flag.rollout_percentage = max(0.0, min(100.0, percentage))
            flag.enabled = flag.rollout_percentage > 0
            return True
        return False

    def get_all(self) -> List[FeatureFlag]:
        return list(self._flags.values())

    def get_enabled(self) -> List[FeatureFlag]:
        return [f for f in self._flags.values() if f.enabled]

    def delete(self, name: str) -> bool:
        return self._flags.pop(name, None) is not None

    def get_stats(self) -> Dict[str, Any]:
        enabled = sum(1 for f in self._flags.values() if f.enabled)
        return {"total": len(self._flags), "enabled": enabled,
                "disabled": len(self._flags) - enabled}
