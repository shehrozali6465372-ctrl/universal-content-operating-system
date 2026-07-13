"""
Environment Loader Module
Layer 1: Core System — Module 3

Manages agent environment with multi-profile support,
validation, auto-reload, and integration with Config & Secrets managers.

Usage:
    from layers.layer01_core.modules.environment_loader import EnvironmentLoader

    env = EnvironmentLoader()
    env.load(profile="development")
    reloaded = env.reload()
    report = env.health_check()
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock
from datetime import datetime, timezone

from layers.layer01_core.modules.env_profiles import (
    get_profile,
    get_available_profiles,
)
from layers.layer01_core.modules.audit_logger import AuditLogger
from layers.layer01_core.modules.exceptions import InvalidConfig


class EnvironmentLoader:
    """
    Loads, validates, and monitors the environment.
    Supports dev/test/prod profiles, auto-reload, and health checking.
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        audit_log_path: str = "logs/audit.log",
    ):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._audit = AuditLogger(str(self._project_root / audit_log_path))
        self._current_profile: Optional[str] = None
        self._env: Dict[str, str] = {}
        self._loaded = False
        self._last_mtime: float = 0.0
        self._lock = Lock()

    # ── Properties ──────────────────────────

    @property
    def current_profile(self) -> Optional[str]:
        return self._current_profile

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def all(self) -> Dict[str, str]:
        return dict(self._env)

    # ── Loading ─────────────────────────────

    def load(
        self,
        profile: str = "development",
        env_file: str = ".env",
    ) -> "EnvironmentLoader":
        """
        Load environment using the specified profile.
        Priority: profile defaults < .env < system vars < AGENT_* vars
        """
        with self._lock:
            profile_obj = get_profile(profile)
            if profile_obj is None:
                raise ValueError(
                    f"Unknown environment profile: '{profile}'. "
                    f"Available: {', '.join(get_available_profiles())}"
                )

            self._current_profile = profile_obj.name
            self._env = {}

            # 1) Apply profile defaults
            for key, value in profile_obj.defaults.items():
                # Only set if not already set (profile defaults are low priority)
                if key not in self._env:
                    self._env[key] = value

            # 2) Load from .env file
            self._load_env_file(self._project_root / env_file)

            # 3) System environment variables override
            for key in profile_obj.required_vars:
                sys_val = os.environ.get(key)
                if sys_val is not None:
                    self._env[key] = sys_val

            # 4) AGENT_ prefix env vars — highest override
            for key, value in os.environ.items():
                if key.startswith("AGENT_"):
                    config_key = key[6:]
                    self._env[config_key] = value

            # 5) Track file mtime for auto-reload
            env_path = self._project_root / env_file
            if env_path.exists():
                self._last_mtime = env_path.stat().st_mtime

            self._loaded = True

        self._audit.log("ENVIRONMENT", f"LOADED ({profile_obj.name})", "SUCCESS")
        return self

    def _load_env_file(self, env_path: Path) -> None:
        """Parse .env file into self._env (overwrites only, file has higher priority)."""
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
                    if key:
                        self._env[key] = value

    # ── Auto-Reload ─────────────────────────

    def reload(self) -> bool:
        """Reload if .env file changed. Returns True if reloaded."""
        env_path = self._project_root / ".env"
        if not env_path.exists():
            return False

        current_mtime = env_path.stat().st_mtime
        if current_mtime > self._last_mtime:
            self.load(profile=self._current_profile or "development")
            self._audit.log("ENVIRONMENT", "RELOADED", "SUCCESS")
            return True
        return False

    # ── Validation ──────────────────────────

    def validate(self) -> List[str]:
        """Validate that all required variables exist for current profile."""
        errors = []
        if self._current_profile is None:
            errors.append("No environment profile loaded")
            return errors

        profile_obj = get_profile(self._current_profile)
        if profile_obj is None:
            errors.append(f"Unknown profile: {self._current_profile}")
            return errors

        for var in profile_obj.required_vars:
            value = self._env.get(var)
            if not value or value.strip() == "":
                errors.append(f"Missing required environment variable: {var}")

        return errors

    def validate_strict(self) -> None:
        """Validate and raise if any errors."""
        errors = self.validate()
        if errors:
            msg = f"Environment validation failed ({len(errors)} error(s)):\n"
            msg += "\n".join(f"  - {e}" for e in errors)
            self._audit.log("ENVIRONMENT", "VALIDATION_FAILED", "FAILED", msg)
            raise InvalidConfig("ENVIRONMENT", msg)

    # ── Access ──────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Get an environment variable."""
        return self._env.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set a runtime environment override."""
        self._env[key] = value

    def has(self, key: str) -> bool:
        return key in self._env

    def get_profile_info(self) -> dict:
        """Get current profile metadata."""
        profile_obj = get_profile(self._current_profile) if self._current_profile else None
        if profile_obj is None:
            return {"name": "unknown", "description": ""}
        return {"name": profile_obj.name, "description": profile_obj.description}

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """
        Full environment health check:
        1. Profile loaded?
        2. Required vars present?
        3. .env file exists and readable?
        4. Auto-reload working?
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }

        # Check 1: Profile
        if self._current_profile:
            report["checks"]["profile"] = {
                "status": "PASS",
                "message": f"Profile: {self._current_profile}",
            }
        else:
            report["checks"]["profile"] = {
                "status": "FAIL",
                "message": "No environment profile loaded",
            }

        # Check 2: Required vars
        errors = self.validate()
        if not errors:
            report["checks"]["required_vars"] = {
                "status": "PASS",
                "message": "All required variables present",
            }
        else:
            report["checks"]["required_vars"] = {
                "status": "FAIL",
                "message": f"Missing {len(errors)} required variable(s)",
                "details": errors,
            }

        # Check 3: .env file
        env_path = self._project_root / ".env"
        if env_path.exists():
            report["checks"]["env_file"] = {
                "status": "PASS",
                "message": f"File exists: {env_path}",
            }
        else:
            report["checks"]["env_file"] = {
                "status": "WARN",
                "message": "No .env file (profile defaults will be used)",
            }

        # Check 4: Auto-reload
        if self._last_mtime > 0:
            report["checks"]["auto_reload"] = {
                "status": "PASS",
                "message": "Auto-reload initialized",
            }
        else:
            report["checks"]["auto_reload"] = {
                "status": "WARN",
                "message": "Auto-reload not active (no .env file to monitor)",
            }

        # Overall status
        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"

        self._audit.log("ENVIRONMENT", "HEALTH_CHECK", report["overall"])
        return report

    # ── Snapshot ────────────────────────────

    def snapshot(self, filepath: str = "data/env_snapshot.json") -> dict:
        """Save current environment state to file."""
        save_path = self._project_root / filepath
        save_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "profile": self._current_profile,
            "variables": {k: "***SECRET***" if "KEY" in k or "TOKEN" in k else v
                          for k, v in self._env.items()},
        }
        with open(save_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        return snapshot

    # ── Reset ───────────────────────────────

    def reset(self) -> None:
        """Reset to unloaded state."""
        with self._lock:
            self._env = {}
            self._current_profile = None
            self._loaded = False
            self._last_mtime = 0.0
        self._audit.log("ENVIRONMENT", "RESET", "SUCCESS")
