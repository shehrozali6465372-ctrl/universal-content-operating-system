"""
Environment Loader Module
Layer 1: Core System — Module 3

Loads environment profiles and non-secret configuration inputs.
Credentials remain managed by Layer 1 SecretsManager.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import RLock
from datetime import datetime, timezone

from layers.layer01_core.modules.env_profiles import (
    get_profile,
    get_available_profiles,
)
from layers.layer01_core.modules.audit_logger import AuditLogger
from layers.layer01_core.modules.exceptions import InvalidConfig

_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


class EnvironmentLoader:
    """Loads, validates, and monitors the environment."""

    def __init__(self, project_root: Optional[str] = None, audit_log_path: str = "logs/audit.log"):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._audit = AuditLogger(str(self._project_root / audit_log_path))
        self._current_profile: Optional[str] = None
        self._env: Dict[str, str] = {}
        self._loaded = False
        self._last_mtime: float = 0.0
        self._env_file: Optional[Path] = None
        self._lock = RLock()

    @property
    def current_profile(self) -> Optional[str]:
        return self._current_profile

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def all(self) -> Dict[str, str]:
        """Return a redacted environment snapshot; raw credentials require explicit get()."""
        with self._lock:
            return {k: self._redact_key(k, v) for k, v in self._env.items()}

    def load(self, profile: str = "development", env_file: str = ".env") -> "EnvironmentLoader":
        """
        Load environment using the specified profile.
        Priority: profile defaults < .env < system vars for profile requirements < AGENT_*.
        """
        with self._lock:
            profile_obj = get_profile(profile)
            if profile_obj is None:
                raise ValueError(
                    f"Unknown environment profile: '{profile}'. "
                    f"Available: {', '.join(get_available_profiles())}"
                )

            self._current_profile = profile_obj.name
            self._env_file = self._project_root / env_file
            self._env = {}

            for key, value in profile_obj.defaults.items():
                self._env[key] = value

            self._load_env_file(self._env_file)

            # Load all explicitly declared system variables so non-required
            # operational settings are not silently ignored.
            for key, value in os.environ.items():
                if key in profile_obj.required_vars or key.startswith("AGENT_"):
                    config_key = key[6:] if key.startswith("AGENT_") else key
                    self._env[config_key] = value

            if self._env_file.exists():
                self._last_mtime = self._env_file.stat().st_mtime
            else:
                self._last_mtime = 0.0

            self._loaded = True

        self._audit.log("ENVIRONMENT", f"LOADED ({profile_obj.name})", "SUCCESS")
        return self

    def _load_env_file(self, env_path: Path) -> None:
        if not env_path.exists():
            return
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    self._env[key] = value

    def reload(self) -> bool:
        """Reload the originally selected env file if it changed."""
        with self._lock:
            if self._env_file is None or not self._env_file.exists():
                return False
            current_mtime = self._env_file.stat().st_mtime
            if current_mtime <= self._last_mtime:
                return False
            profile = self._current_profile or "development"
        self.load(profile=profile, env_file=str(self._env_file.relative_to(self._project_root)))
        self._audit.log("ENVIRONMENT", "RELOADED", "SUCCESS")
        return True

    def validate(self) -> List[str]:
        errors = []
        if self._current_profile is None:
            return ["No environment profile loaded"]

        profile_obj = get_profile(self._current_profile)
        if profile_obj is None:
            return [f"Unknown profile: {self._current_profile}"]

        for var in profile_obj.required_vars:
            value = self._env.get(var)
            if not value or value.strip() == "":
                errors.append(f"Missing required environment variable: {var}")
        return errors

    def validate_strict(self) -> None:
        errors = self.validate()
        if errors:
            msg = f"Environment validation failed ({len(errors)} error(s)):\n"
            msg += "\n".join(f"  - {e}" for e in errors)
            self._audit.log("ENVIRONMENT", "VALIDATION_FAILED", "FAILED", msg)
            raise InvalidConfig("ENVIRONMENT", msg)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._env.get(key, default)

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._env[key] = value

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._env

    def get_profile_info(self) -> dict:
        profile_obj = get_profile(self._current_profile) if self._current_profile else None
        if profile_obj is None:
            return {"name": "unknown", "description": ""}
        return {"name": profile_obj.name, "description": profile_obj.description}

    def health_check(self) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        report["checks"]["profile"] = (
            {"status": "PASS", "message": f"Profile: {self._current_profile}"}
            if self._current_profile
            else {"status": "FAIL", "message": "No environment profile loaded"}
        )

        errors = self.validate()
        report["checks"]["required_vars"] = (
            {"status": "PASS", "message": "All required variables present"}
            if not errors
            else {"status": "FAIL", "message": f"Missing {len(errors)} required variable(s)", "details": errors}
        )

        if self._env_file and self._env_file.exists():
            report["checks"]["env_file"] = {
                "status": "PASS",
                "message": f"File exists: {self._env_file}",
            }
        else:
            report["checks"]["env_file"] = {
                "status": "WARN",
                "message": "No .env file (profile defaults will be used)",
            }

        report["checks"]["auto_reload"] = (
            {"status": "PASS", "message": "Auto-reload initialized"}
            if self._last_mtime > 0
            else {"status": "WARN", "message": "Auto-reload not active (no .env file to monitor)"}
        )

        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"

        self._audit.log("ENVIRONMENT", "HEALTH_CHECK", report["overall"])
        return report

    def _redact_key(self, key: str, value: str) -> str:
        normalized = key.upper()
        terminal = normalized.rsplit(".", 1)[-1]
        secret = (
            terminal.endswith("_KEY")
            or terminal.endswith("_TOKEN")
            or terminal.endswith("_SECRET")
            or terminal.endswith("_PASSWORD")
            or terminal.endswith("_CREDENTIAL")
            or terminal in {"KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"}
            or terminal in {"OPENAI_API_KEY", "FACEBOOK_ACCESS_TOKEN", "GITHUB_TOKEN", "GITHUB_ACCESS_TOKEN", "MASTER_KEY", "AGENT_MASTER_KEY"}
        )
        return "***SECRET***" if secret else value

    def snapshot(self, filepath: str = "data/env_snapshot.json") -> dict:
        """Atomically save a secret-redacted environment snapshot."""
        save_path = self._project_root / filepath
        save_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "profile": self._current_profile,
            "variables": {k: self._redact_key(k, v) for k, v in self._env.items()},
        }
        fd, tmp_name = tempfile.mkstemp(
            dir=str(save_path.parent),
            prefix=f".{save_path.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, save_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return snapshot

    def reset(self) -> None:
        with self._lock:
            self._env = {}
            self._current_profile = None
            self._loaded = False
            self._last_mtime = 0.0
            self._env_file = None
        self._audit.log("ENVIRONMENT", "RESET", "SUCCESS")
