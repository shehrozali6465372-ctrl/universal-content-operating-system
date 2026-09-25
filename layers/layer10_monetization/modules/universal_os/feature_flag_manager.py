"""FeatureFlagManager — validated feature flags and rollout configuration."""
from __future__ import annotations
from typing import Any, Dict, List


class FeatureFlag:
    def __init__(self, name: str, enabled: bool = False) -> None:
        self.name = name
        self.enabled = enabled
        self.description = ""
        self.rollout_percentage = 100.0 if enabled else 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "enabled": self.enabled,
                "rollout_percentage": self.rollout_percentage,
                "description": self.description}


class FeatureFlagManager:
    """Manage flags; rollout percentage is configuration, not a fake activation claim."""

    def __init__(self) -> None:
        self._flags: Dict[str, FeatureFlag] = {}

    def create(self, name: str, enabled: bool = False, description: str = "",
               rollout_percentage: float = 100.0) -> FeatureFlag:
        if not name:
            raise ValueError("name is required")
        if not 0 <= rollout_percentage <= 100:
            raise ValueError("rollout_percentage must be between 0 and 100")
        if name in self._flags:
            return self._flags[name]
        flag = FeatureFlag(name, enabled)
        flag.description = description
        flag.rollout_percentage = rollout_percentage if enabled else 0.0
        self._flags[name] = flag
        return flag

    def enable(self, name: str) -> bool:
        flag = self._flags.get(name)
        if flag is None:
            return False
        flag.enabled = True
        if flag.rollout_percentage == 0:
            flag.rollout_percentage = 100.0
        return True

    def disable(self, name: str) -> bool:
        flag = self._flags.get(name)
        if flag is None:
            return False
        flag.enabled = False
        return True

    def is_enabled(self, name: str) -> bool:
        flag = self._flags.get(name)
        return flag is not None and flag.enabled and flag.rollout_percentage > 0

    def set_rollout(self, name: str, percentage: float) -> bool:
        if not 0 <= percentage <= 100:
            raise ValueError("percentage must be between 0 and 100")
        flag = self._flags.get(name)
        if flag is None:
            return False
        flag.rollout_percentage = percentage
        if percentage == 0:
            flag.enabled = False
        return True

    def get_all(self) -> List[FeatureFlag]:
        return list(self._flags.values())

    def get_enabled(self) -> List[FeatureFlag]:
        return [flag for flag in self._flags.values() if self.is_enabled(flag.name)]

    def delete(self, name: str) -> bool:
        return self._flags.pop(name, None) is not None

    def get_stats(self) -> Dict[str, Any]:
        enabled = sum(self.is_enabled(flag.name) for flag in self._flags.values())
        return {"total": len(self._flags), "enabled": enabled,
                "disabled": len(self._flags) - enabled}
