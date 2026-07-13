"""
Settings Manager Exceptions
Layer 1: Core System — Module 9
"""


class SettingsError(Exception):
    """Base exception for settings manager."""


class SettingNotFoundError(SettingsError):
    """Raised when a requested setting does not exist."""


class SettingValidationError(SettingsError):
    """Raised when a setting value fails validation."""


class SettingImmutableError(SettingsError):
    """Raised when trying to modify an immutable setting."""


class InvalidFeatureFlagError(SettingsError):
    """Raised when feature flag configuration is invalid."""


class RollbackError(SettingsError):
    """Raised when rollback fails."""


class SettingsLoadError(SettingsError):
    """Raised when settings file cannot be loaded."""
