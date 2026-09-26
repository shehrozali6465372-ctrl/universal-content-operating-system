"""Environment management with secret-safe storage and activation semantics."""
from __future__ import annotations
import os
from enum import Enum
from typing import Any, Dict, List, Optional

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class EnvironmentConfig:
    __slots__ = ("env", "variables", "secret_keys", "active", "metadata")
    def __init__(self, env: Environment) -> None:
        self.env = env
        self.variables: Dict[str, str] = {}
        self.secret_keys: set[str] = set()
        self.active = False
        self.metadata: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"environment": self.env.value, "variables": len(self.variables),
                "secrets_count": len(self.secret_keys), "active": self.active}

class EnvironmentManager:
    """Owns environment metadata; secret values are never returned by status APIs."""
    def __init__(self) -> None:
        self._environments: Dict[str, EnvironmentConfig] = {}
        self._current: Optional[str] = None
    def create(self, env: Environment) -> EnvironmentConfig:
        if env.value in self._environments:
            raise ValueError(f"Environment already exists: {env.value}")
        config = EnvironmentConfig(env)
        self._environments[env.value] = config
        return config
    def set_variable(self, env_name: str, key: str, value: str, *, secret: bool = False) -> bool:
        config = self._environments.get(env_name)
        if config is None:
            return False
        if not key or "\x00" in key or "\x00" in value:
            raise ValueError("Environment keys and values must be non-empty and NUL-free")
        config.variables[key] = value
        if secret:
            config.secret_keys.add(key)
        else:
            config.secret_keys.discard(key)
        return True
    def get_variable(self, env_name: str, key: str) -> Optional[str]:
        config = self._environments.get(env_name)
        return config.variables.get(key) if config else None
    def get_secret(self, env_name: str, key: str) -> Optional[str]:
        config = self._environments.get(env_name)
        if config is None or key not in config.secret_keys:
            return None
        return config.variables.get(key)
    def load_from_os(self, env: Environment, prefix: str = "") -> EnvironmentConfig:
        config = self._environments.get(env.value) or self.create(env)
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            normalized = key[len(prefix):] if prefix else key
            self.set_variable(env.value, normalized, value, secret=self._looks_secret(normalized))
        return config
    @staticmethod
    def _looks_secret(key: str) -> bool:
        upper = key.upper()
        return any(token in upper for token in ("KEY", "TOKEN", "PASSWORD", "SECRET", "PRIVATE"))
    def activate(self, env_name: str) -> bool:
        config = self._environments.get(env_name)
        if config is None:
            return False
        if env_name == Environment.PRODUCTION.value:
            missing = {"POSTGRES_PASSWORD"} - config.variables.keys()
            if missing:
                raise ValueError("Production activation missing required secrets")
        for item in self._environments.values():
            item.active = False
        config.active = True
        self._current = env_name
        return True
    def get_current(self) -> Optional[str]:
        return self._current
    def list_environments(self) -> List[Dict[str, Any]]:
        return [config.to_dict() for config in self._environments.values()]
