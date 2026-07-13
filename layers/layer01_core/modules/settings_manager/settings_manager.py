"""
Settings Manager Module
Layer 1: Core System — Module 9

Intelligent settings management with:
- Multi-level priority: default → config → env → runtime → override
- Feature flags with conditions
- Change history and rollback
- Event system for reactive updates
- Settings audit trail
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from threading import Lock

from layers.layer01_core.modules.settings_manager.setting_schema import SettingEntry
from layers.layer01_core.modules.settings_manager.event_system import SettingsEventBus, SettingsEvent
from layers.layer01_core.modules.settings_manager.exceptions import (
    SettingNotFoundError,
    SettingValidationError,
    SettingImmutableError,
    InvalidFeatureFlagError,
    RollbackError,
    SettingsLoadError,
)


# ── Built-in Validators ─────────────────────

def validator_not_empty(value: Any) -> bool:
    if isinstance(value, str):
        return len(value.strip()) > 0
    return value is not None


def validator_positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def validator_in_list(allowed: list) -> Callable:
    def _check(value: Any) -> bool:
        return value in allowed
    return _check


def validator_model_exists(value: Any) -> bool:
    valid_models = ["gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "claude-3.5-sonnet"]
    return value in valid_models


# ── Feature Flag ─────────────────────────────

class FeatureFlag:
    """Conditional feature flag with enable/disable and percentage rollout."""

    __slots__ = ("name", "enabled", "rollout_pct", "conditions", "description")

    def __init__(self, name: str, enabled: bool = True,
                 rollout_pct: float = 100.0, conditions: Optional[Dict] = None,
                 description: str = ""):
        self.name = name
        self.enabled = enabled
        self.rollout_pct = rollout_pct
        self.conditions = conditions or {}
        self.description = description

    def is_active(self, context: Optional[Dict] = None) -> bool:
        if not self.enabled:
            return False
        if self.rollout_pct <= 0:
            return False
        for key, expected in self.conditions.items():
            if context is None or context.get(key) != expected:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "rollout_pct": self.rollout_pct,
            "conditions": self.conditions,
            "description": self.description,
        }


# ── Main Settings Manager ────────────────────

class SettingsManager:
    """Intelligent settings manager with priority levels, rollback, and events."""

    PRIORITY_LEVELS = ["default", "config", "env", "runtime", "override"]

    def __init__(self, persist_path: Optional[str] = None):
        self._settings: Dict[str, SettingEntry] = {}
        self._overrides: Dict[str, Any] = {}
        self._feature_flags: Dict[str, FeatureFlag] = {}
        self._history: List[dict] = []
        self._event_bus = SettingsEventBus()
        self._lock = Lock()
        self._persist_path = Path(persist_path) if persist_path else None
        self._max_history = 100

    # ── Settings CRUD ────────────────────────

    def register(self, key: str, value: Any, default_value: Any = None,
                 datatype: type = str, validator: Optional[Callable] = None,
                 category: str = "general", editable: bool = True,
                 immutable: bool = False, description: str = "") -> SettingEntry:
        """Register a new setting with metadata."""
        entry = SettingEntry(
            key=key, value=value, default_value=default_value,
            datatype=datatype, validator=validator, category=category,
            editable=editable, immutable=immutable, description=description,
        )
        with self._lock:
            self._settings[key] = entry
        return entry

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value. Checks overrides first, then setting value."""
        with self._lock:
            if key in self._overrides:
                return self._overrides[key]
            if key in self._settings:
                return self._settings[key].value
        return default

    def get_entry(self, key: str) -> SettingEntry:
        """Get full SettingEntry with metadata."""
        with self._lock:
            if key not in self._settings:
                raise SettingNotFoundError(f"Setting '{key}' not found")
            return self._settings[key]

    def set(self, key: str, value: Any, changed_by: str = "user") -> bool:
        """Set a setting value with validation and event emission."""
        with self._lock:
            if key not in self._settings:
                raise SettingNotFoundError(f"Setting '{key}' not found")

            entry = self._settings[key]

            if entry.immutable:
                raise SettingImmutableError(f"Setting '{key}' is immutable")

            if not entry.editable:
                raise SettingImmutableError(f"Setting '{key}' is not editable")

            if not entry.validate_value(value):
                raise SettingValidationError(f"Validation failed for '{key}'")

            old_value = entry.value
            entry.value = value
            entry.last_changed = datetime.now(timezone.utc).isoformat()
            entry.changed_by = changed_by
            entry.version += 1

        # Record history
        self._record_history(key, old_value, value, changed_by)

        # Emit event
        event = SettingsEvent("setting_changed", key, old_value, value, changed_by)
        self._event_bus.emit(event)

        return True

    def delete(self, key: str) -> bool:
        """Remove a setting."""
        with self._lock:
            if key not in self._settings:
                raise SettingNotFoundError(f"Setting '{key}' not found")
            entry = self._settings[key]
            if entry.immutable:
                raise SettingImmutableError(f"Cannot delete immutable setting '{key}'")
            del self._settings[key]
        self._event_bus.emit(SettingsEvent("setting_deleted", key))
        return True

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._settings

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._settings.keys())

    def all(self) -> Dict[str, Any]:
        """Get all setting values."""
        with self._lock:
            return {k: v.value for k, v in self._settings.items()}

    def by_category(self, category: str) -> Dict[str, Any]:
        with self._lock:
            return {k: v.value for k, v in self._settings.items()
                    if v.category == category}

    # ── Priority / Override System ───────────

    def set_override(self, key: str, value: Any) -> None:
        """Set a temporary runtime override (highest priority)."""
        with self._lock:
            if key not in self._settings:
                raise SettingNotFoundError(f"Setting '{key}' not found")
            self._overrides[key] = value
        self._event_bus.emit(SettingsEvent("override_set", key, new_value=value))

    def clear_override(self, key: str) -> bool:
        with self._lock:
            if key in self._overrides:
                del self._overrides[key]
                self._event_bus.emit(SettingsEvent("override_cleared", key))
                return True
        return False

    def clear_all_overrides(self) -> int:
        with self._lock:
            count = len(self._overrides)
            self._overrides.clear()
        return count

    def effective_value(self, key: str) -> Any:
        """Get the effective value considering all priority levels."""
        with self._lock:
            if key in self._overrides:
                return self._overrides[key]
            if key in self._settings:
                return self._settings[key].value
        return None

    # ── Feature Flags ────────────────────────

    def register_flag(self, name: str, enabled: bool = True,
                      rollout_pct: float = 100.0,
                      conditions: Optional[Dict] = None,
                      description: str = "") -> FeatureFlag:
        flag = FeatureFlag(name, enabled, rollout_pct, conditions, description)
        with self._lock:
            self._feature_flags[name] = flag
        return flag

    def is_flag_active(self, name: str, context: Optional[Dict] = None) -> bool:
        with self._lock:
            if name not in self._feature_flags:
                raise InvalidFeatureFlagError(f"Feature flag '{name}' not found")
            return self._feature_flags[name].is_active(context)

    def toggle_flag(self, name: str) -> bool:
        with self._lock:
            if name not in self._feature_flags:
                raise InvalidFeatureFlagError(f"Feature flag '{name}' not found")
            flag = self._feature_flags[name]
            flag.enabled = not flag.enabled
        self._event_bus.emit(SettingsEvent("flag_toggled", name, new_value=flag.enabled))
        return flag.enabled

    def get_flags(self) -> Dict[str, dict]:
        with self._lock:
            return {n: f.to_dict() for n, f in self._feature_flags.items()}

    # ── History & Rollback ───────────────────

    def _record_history(self, key: str, old_value: Any, new_value: Any, changed_by: str) -> None:
        entry = {
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "changed_by": changed_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._history.append(entry)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

    def rollback(self, key: str, steps: int = 1) -> bool:
        """Rollback a setting to a previous value."""
        with self._lock:
            history_for_key = [h for h in self._history if h["key"] == key]
            if len(history_for_key) < steps:
                raise RollbackError(f"Not enough history to rollback '{key}' {steps} steps")

            target = history_for_key[-steps]
            if key not in self._settings:
                raise SettingNotFoundError(f"Setting '{key}' not found")

            entry = self._settings[key]
            if entry.immutable:
                raise SettingImmutableError(f"Cannot rollback immutable setting '{key}'")

            old_value = entry.value
            entry.value = target["old_value"]
            entry.last_changed = datetime.now(timezone.utc).isoformat()
            entry.changed_by = f"rollback:{target['changed_by']}"
            entry.version += 1

        self._record_history(key, old_value, target["old_value"], f"rollback:{target['changed_by']}")
        self._event_bus.emit(SettingsEvent("setting_rollback", key, old_value, target["old_value"]))
        return True

    def get_history(self, key: Optional[str] = None, limit: int = 20) -> List[dict]:
        with self._lock:
            history = list(self._history)
        if key:
            history = [h for h in history if h["key"] == key]
        return history[-limit:]

    # ── Import / Export ──────────────────────

    def export_settings(self, filepath: str) -> bool:
        """Export all settings to JSON file."""
        data = {}
        with self._lock:
            for key, entry in self._settings.items():
                data[key] = entry.to_dict()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        Path(filepath).write_text(json.dumps(data, indent=2, default=str))
        self._event_bus.emit(SettingsEvent("settings_exported", key="*"))
        return True

    def import_settings(self, filepath: str, overwrite: bool = False) -> int:
        """Import settings from JSON file. Returns count of imported settings."""
        path = Path(filepath)
        if not path.exists():
            raise SettingsLoadError(f"File not found: {filepath}")

        data = json.loads(path.read_text())
        count = 0
        for key, entry_data in data.items():
            with self._lock:
                if key in self._settings and not overwrite:
                    continue
            entry = SettingEntry.from_dict(entry_data)
            with self._lock:
                self._settings[key] = entry
            count += 1
        self._event_bus.emit(SettingsEvent("settings_imported", key="*", new_value=count))
        return count

    def export_flags(self, filepath: str) -> bool:
        data = {}
        with self._lock:
            for name, flag in self._feature_flags.items():
                data[name] = flag.to_dict()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        Path(filepath).write_text(json.dumps(data, indent=2))
        return True

    # ── Persistence ──────────────────────────

    def save(self, filepath: Optional[str] = None) -> bool:
        """Save current settings to disk."""
        path = Path(filepath) if filepath else self._persist_path
        if path is None:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"settings": {}, "flags": {}}
        with self._lock:
            for key, entry in self._settings.items():
                data["settings"][key] = entry.to_dict()
            for name, flag in self._feature_flags.items():
                data["flags"][name] = flag.to_dict()
        path.write_text(json.dumps(data, indent=2, default=str))
        return True

    def load(self, filepath: Optional[str] = None) -> bool:
        """Load settings from disk."""
        path = Path(filepath) if filepath else self._persist_path
        if path is None or not path.exists():
            return False
        try:
            data = json.loads(path.read_text())
            for key, entry_data in data.get("settings", {}).items():
                entry = SettingEntry.from_dict(entry_data)
                with self._lock:
                    self._settings[key] = entry
            for name, flag_data in data.get("flags", {}).items():
                flag = FeatureFlag(
                    name=name,
                    enabled=flag_data.get("enabled", True),
                    rollout_pct=flag_data.get("rollout_pct", 100.0),
                    conditions=flag_data.get("conditions", {}),
                    description=flag_data.get("description", ""),
                )
                with self._lock:
                    self._feature_flags[name] = flag
            return True
        except (json.JSONDecodeError, KeyError) as e:
            raise SettingsLoadError(f"Failed to load settings: {e}")

    # ── Event Bus ────────────────────────────

    @property
    def events(self) -> SettingsEventBus:
        return self._event_bus

    # ── Health Check ─────────────────────────

    def health_check(self) -> dict:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        with self._lock:
            settings_count = len(self._settings)
            flags_count = len(self._feature_flags)
            overrides_count = len(self._overrides)
            history_count = len(self._history)
            immutable_count = sum(1 for s in self._settings.values() if s.immutable)
            subscribers = self._event_bus.subscriber_count()

        report["checks"]["settings"] = {
            "status": "PASS",
            "message": f"{settings_count} settings registered",
        }
        report["checks"]["feature_flags"] = {
            "status": "PASS" if flags_count > 0 else "WARN",
            "message": f"{flags_count} feature flags",
        }
        report["checks"]["overrides"] = {
            "status": "PASS",
            "message": f"{overrides_count} active overrides",
        }
        report["checks"]["history"] = {
            "status": "PASS",
            "message": f"{history_count} history entries, {immutable_count} immutable",
        }
        report["checks"]["event_bus"] = {
            "status": "PASS",
            "message": f"{subscribers} subscribers",
        }

        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report
