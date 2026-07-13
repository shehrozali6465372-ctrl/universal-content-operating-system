"""
Settings Manager Module
Layer 1: Core System — Module 9

Intelligent settings management with:
- Multi-level priority (default → config → env → runtime → override)
- Feature flags with conditions
- Change history and rollback
- Event system for reactive updates
- Settings audit trail
"""

from layers.layer01_core.modules.settings_manager.settings_manager import SettingsManager
from layers.layer01_core.modules.settings_manager.setting_schema import SettingEntry
from layers.layer01_core.modules.settings_manager.event_system import SettingsEventBus

__all__ = ["SettingsManager", "SettingEntry", "SettingsEventBus"]
