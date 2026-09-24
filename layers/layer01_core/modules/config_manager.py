"""
Config Manager Module
Layer 1: Core System

Central configuration manager with:
- Multi-source loading (.env + YAML + env vars)
- Immutable settings protection
- Config versioning for migration support
- Schema validation
- Secret-safe persistence
"""

import os
import tempfile
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

# Values for these keys are credentials and must never be persisted by the
# configuration plane. Layer 1 SecretsManager is the credential source of truth.
SECRET_KEYS = frozenset({
    "OPENAI_API_KEY",
    "FACEBOOK_ACCESS_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_ACCESS_TOKEN",
    "MASTER_KEY",
    "AGENT_MASTER_KEY",
})


class ConfigManager:
    """Singleton config manager with immutable protection and versioning."""

    _instances: Dict[tuple, "ConfigManager"] = {}
    _lock = Lock()

    def __new__(cls, project_root: Optional[str] = None, admin_mode: bool = False, *args, **kwargs):
        root = str(Path(project_root).resolve()) if project_root else str(Path(__file__).resolve().parents[3])
        key = (root, bool(admin_mode))
        with cls._lock:
            instance = cls._instances.get(key)
            if instance is None:
                instance = super().__new__(cls)
                cls._instances[key] = instance
            return instance

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

    def _safe_path(self, value: str) -> Path:
        candidate = (self._project_root / value).resolve()
        try:
            candidate.relative_to(self._project_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Config path escapes project root: {value}") from exc
        return candidate

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def config_version(self) -> int:
        return self._config.get("CONFIG_VERSION", CONFIG_VERSION)

    def load(self, env_file: str = ".env", yaml_file: str = "config/default.yaml") -> "ConfigManager":
        self._config.clear()
        self._load_yaml(self._safe_path(yaml_file))
        self._load_env(self._safe_path(env_file))

        defaults = get_defaults()
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

        self._apply_env_overrides()

        self._config["CONFIG_VERSION"] = CONFIG_VERSION
        self._loaded = True
        return self

    def _load_yaml(self, yaml_path: Path) -> None:
        if not yaml_path.exists():
            return
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, dict):
            self._flatten_dict(data)

    def _load_env(self, env_path: Path) -> None:
        if not env_path.exists():
            return
        with open(env_path, "r", encoding="utf-8") as f:
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

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set config value. Blocked for immutable keys unless admin_mode."""
        if key in IMMUTABLE_KEYS and not self._admin_mode:
            raise InvalidConfig(
                key,
                f"'{key}' is immutable and cannot be changed at runtime. "
                f"Use admin_mode=True to override."
            )
        self._config[key] = value

    def has(self, key: str) -> bool:
        return key in self._config

    def all(self) -> Dict[str, Any]:
        """Return a redacted configuration snapshot; raw credentials require explicit get()."""
        return {
            key: ("***SECRET***" if self._is_secret_key(key) else value)
            for key, value in self._config.items()
        }

    @staticmethod
    def _is_secret_key(key: str) -> bool:
        terminal = key.upper().rsplit(".", 1)[-1]
        return (
            terminal in SECRET_KEYS
            or terminal.endswith("_API_KEY")
            or terminal.endswith("_TOKEN")
            or terminal.endswith("_SECRET")
            or terminal.endswith("_PASSWORD")
            or terminal.endswith("_CREDENTIAL")
        )

    def get_immutable_keys(self) -> List[str]:
        return list(IMMUTABLE_KEYS)

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
                except InvalidConfig as e:
                    errors.append(str(e))
        return errors

    def validate_strict(self) -> None:
        errors = self.validate()
        if errors:
            raise SchemaError(errors)

    def _safe_persist_config(self) -> Dict[str, Any]:
        """Return configuration without credentials; SecretsManager owns them."""
        return {
            key: value
            for key, value in self._config.items()
            if not self._is_secret_key(key)
        }

    def save(self, filepath: str = "config/agent_config.json") -> None:
        """Atomically persist non-secret configuration; credential keys are excluded."""
        save_path = self._safe_path(filepath)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(save_path.parent),
            prefix=f".{save_path.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._safe_persist_config(), f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, save_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instances.clear()
