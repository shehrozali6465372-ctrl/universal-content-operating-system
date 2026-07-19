"""EnvironmentManager — manage deployment environments."""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"; STAGING = "staging"; PRODUCTION = "production"


class EnvironmentConfig:
    __slots__ = ("env", "variables", "secrets_count", "active", "metadata")

    def __init__(self, env: Environment) -> None:
        self.env = env
        self.variables: Dict[str, str] = {}
        self.secrets_count = 0
        self.active = False
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"environment": self.env.value, "variables": len(self.variables),
                "active": self.active}


class EnvironmentManager:
    def __init__(self) -> None:
        self._environments: Dict[str, EnvironmentConfig] = {}
        self._current: Optional[str] = None

    def create(self, env: Environment) -> EnvironmentConfig:
        config = EnvironmentConfig(env)
        self._environments[env.value] = config
        return config

    def set_variable(self, env_name: str, key: str, value: str) -> bool:
        config = self._environments.get(env_name)
        if config:
            config.variables[key] = value
            return True
        return False

    def get_variable(self, env_name: str, key: str) -> Optional[str]:
        config = self._environments.get(env_name)
        return config.variables.get(key) if config else None

    def activate(self, env_name: str) -> bool:
        for config in self._environments.values():
            config.active = False
        config = self._environments.get(env_name)
        if config:
            config.active = True
            self._current = env_name
            return True
        return False

    def get_current(self) -> Optional[str]:
        return self._current

    def list_environments(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._environments.values()]
