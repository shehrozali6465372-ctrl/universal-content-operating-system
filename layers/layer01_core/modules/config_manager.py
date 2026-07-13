"""
Config Manager Module
Layer 1: Core System

Central configuration manager that loads from .env + YAML,
validates against schema, and provides global access.

Usage:
    from layers.layer01_core.modules.config_manager import ConfigManager

    config = ConfigManager()
    config.load()
    print(config.get("OPENAI_API_KEY"))
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
    get_required_keys,
)
from layers.layer01_core.modules.validators import validate_config_value
from layers.layer01_core.modules.exceptions import (
    ConfigNotFound,
    MissingAPIKey,
    SchemaError,
)


class ConfigManager:
    """Singleton config manager with validation and multi-source loading."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, project_root: Optional[str] = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self._project_root = (
            Path(project_root) if project_root
            else Path(__file__).resolve().parents[3]
        )
        self._config: Dict[str, Any] = {}
        self._loaded = False

    # ── Properties ──────────────────────────

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Loading ─────────────────────────────

    def load(self, env_file: str = ".env", yaml_file: str = "config/default.yaml") -> "ConfigManager":
        """Load config from YAML + .env + environment variables."""
        self._config.clear()

        # 1) Load YAML defaults
        self._load_yaml(self._project_root / yaml_file)

        # 2) Load .env file
        self._load_env(self._project_root / env_file)

        # 3) Apply schema defaults for missing optional keys
        defaults = get_defaults()
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

        # 4) Apply environment overrides (AGENT_ prefix)
        self._apply_env_overrides()

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
        self._config[key] = value

    def has(self, key: str) -> bool:
        return key in self._config

    def all(self) -> Dict[str, Any]:
        return dict(self._config)

    # ── Validation ──────────────────────────

    def validate(self) -> List[str]:
        """Validate all fields against schema. Returns list of errors."""
        errors = []
        fields = get_all_fields()

        for field_def in fields:
            value = self._config.get(field_def.key)

            # Check required
            if field_def.required and (value is None or value == ""):
                errors.append(f"Missing required key: {field_def.key}")
                continue

            # Skip validation if optional and not set
            if value is None:
                continue

            # Run validator
            if field_def.validator:
                try:
                    validate_config_value(field_def.key, value, field_def.validator)
                except Exception as e:
                    errors.append(str(e))

        return errors

    def validate_strict(self) -> None:
        """Validate and raise SchemaError if any errors."""
        errors = self.validate()
        if errors:
            raise SchemaError(errors)

    # ── Save ────────────────────────────────

    def save(self, filepath: str = "config/agent_config.json") -> None:
        """Save current config to JSON file."""
        save_path = self._project_root / filepath
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(self._config, f, indent=2, default=str)

    # ── Reset ───────────────────────────────

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None
