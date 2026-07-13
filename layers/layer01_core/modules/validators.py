from typing import Any
"""
Config Validators
Layer 1: Core System

Validates configuration values against defined rules.
"""

from pathlib import Path
from layers.layer01_core.modules.exceptions import InvalidConfig


def validate_not_empty(key: str, value: Any) -> None:
    """Check value is not empty or None."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise InvalidConfig(key, "Value cannot be empty")


def validate_api_key(key: str, value: str) -> None:
    """Check API key format (sk- for OpenAI, gho_ for GitHub)."""
    if not value:
        raise InvalidConfig(key, "API key cannot be empty")
    valid_prefixes = ("sk-", "sk_live-", "gho_", "ghp_", "ghs_")
    if not any(value.startswith(p) for p in valid_prefixes):
        raise InvalidConfig(key, f"API key must start with: {', '.join(valid_prefixes)}")


def validate_path(key: str, value: str) -> None:
    """Check if file or parent directory path is valid."""
    if not value:
        raise InvalidConfig(key, "Path cannot be empty")
    path = Path(value)
    if not path.parent.exists():
        raise InvalidConfig(key, f"Parent directory does not exist: {path.parent}")


def validate_log_level(key: str, value: str) -> None:
    """Check if log level is valid."""
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if value.upper() not in valid_levels:
        raise InvalidConfig(key, f"Must be one of: {', '.join(valid_levels)}")


def validate_bool(key: str, value: Any) -> None:
    """Check if value is a valid boolean."""
    valid_values = {True, False, "true", "false", "1", "0", "yes", "no"}
    if value not in valid_values:
        raise InvalidConfig(key, f"Must be a boolean value: {valid_values}")


def validate_number(key: str, value: Any, min_val: float = None, max_val: float = None) -> None:
    """Check if value is a valid number within range."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise InvalidConfig(key, f"Must be a number, got: {type(value).__name__}")
    if min_val is not None and num < min_val:
        raise InvalidConfig(key, f"Must be >= {min_val}, got: {num}")
    if max_val is not None and num > max_val:
        raise InvalidConfig(key, f"Must be <= {max_val}, got: {num}")


def validate_config_value(key: str, value: Any, validator_name: str) -> None:
    """Route to the correct validator by name."""
    validators = {
        "not_empty": lambda k, v: validate_not_empty(k, v),
        "api_key": lambda k, v: validate_api_key(k, v),
        "path": lambda k, v: validate_path(k, v),
        "log_level": lambda k, v: validate_log_level(k, v),
        "bool": lambda k, v: validate_bool(k, v),
        "number": lambda k, v: validate_number(k, v),
    }
    if validator_name in validators:
        validators[validator_name](key, value)
