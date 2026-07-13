"""
Config Manager Module
Layer 1: Core System

Central configuration manager with:
- Multi-source loading (.env + YAML + env vars)
- Immutable settings protection
- Config versioning for migration support
- Schema validation
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Optional, Dict, List
from threading import Lock

from layers.layer01_core.modules.config_schema import (
    get_all_fields,
    get_defaults,
)
from layers.layer01_core.modules.immutable_settings import IMMUTABLE_KEYS
from layers.layer01_core.modules.validators import validate_config_value
from layers.layer01_core.modules.exceptions import (
    InvalidConfig,
    SchemaError,
)

CONFIG_VERSION = 1


class ConfigManager:
    """Singleton config manager with immutable protection and versioning."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, project_root: Optional[str] = None, admin_mode: bool = False):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._project_root = (
            Path(project_root) if project_root
            else Path(__file__).resolve().parents[3]
        )
        self._config: Dict[str, Any] = {}
        self._admin_mode = admin_mode
        self._loaded = False

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def config_version(self) -> int:
        return self._config.get("CONFIG_VERSION", CONFIG_VERSION)

    # ── Loading ─────────────────────────────

    def load(self, env_file: str = ".env", yaml_file: str = "config/default.yaml") -> "ConfigManager":
        self._config.clear()
        self._load_yaml(self._project_root / yaml_file)
        self._load_env(self._project_root / env_file)

        defaults = get_defaults()
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

        self._apply_env_overrides()

        # Always set config version
        self._config["CONFIG_VERSION"] = CONFIG_VERSION

        self._loaded = True
        return self

    def _load_yaml(self, yaml_path: Path) -> None:
        if not yaml_path.exists():
            return
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, dict):
            self._flatten_dict(data)

    def _load_env(self, env_path: Path) -> None:
        if not env_path.exists():
            return
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    self._config[key] = value

    def _apply_env_overrides(self) -> None:
        for key, value in os.environ.items():
            if key.startswith("AGENT_"):
                config_key = key[6:]
                self._config[config_key] = value

    def _flatten_dict(self, d: dict, prefix: str = "") -> None:
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_dict(value, full_key)
            else:
                self._config[full_key] = value

    # ── Access ──────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set config value. Blocked for immutable keys unless admin_mode."""
        if key in IMMUTABLE_KEYS:
            if not self._admin_mode:
                raise InvalidConfig(
                    key,
                    f"'{key}' is immutable and cannot be changed at runtime. "
                    f"Use admin_mode=True to override."
                )
        self._config[key] = value

    def has(self, key: str) -> bool:
        return key in self._config

    def all(self) -> Dict[str, Any]:
        return dict(self._config)

    def get_immutable_keys(self) -> List[str]:
        return list(IMMUTABLE_KEYS)

    # ── Validation ──────────────────────────

    def validate(self) -> List[str]:
        errors = []
        fields = get_all_fields()
        for field_def in fields:
            value = self._config.get(field_def.key)
            if field_def.required and (value is None or value == ""):
                errors.append(f"Missing required key: {field_def.key}")
                continue
            if value is None:
                continue
            if field_def.validator:
                try:
                    validate_config_value(field_def.key, value, field_def.validator)
                except Exception as e:
                    errors.append(str(e))
        return errors

    def validate_strict(self) -> None:
        errors = self.validate()
        if errors:
            raise SchemaError(errors)

    # ── Save ────────────────────────────────

    def save(self, filepath: str = "config/agent_config.json") -> None:
        save_path = self._project_root / filepath
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(self._config, f, indent=2, default=str)

    # ── Reset ───────────────────────────────

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None
