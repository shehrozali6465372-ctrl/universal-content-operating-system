import math
from typing import Any
from pathlib import Path

from layers.layer01_core.modules.exceptions import InvalidConfig


def validate_not_empty(key: str, value: Any) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise InvalidConfig(key, "Value cannot be empty")


def validate_api_key(key: str, value: str) -> None:
    """Validate known credential formats without logging or exposing values."""
    if not value:
        raise InvalidConfig(key, "API key cannot be empty")
    # Layer 1 must not guess provider-specific credential formats. Provider
    # adapters own format validation; the core contract only requires a
    # non-empty string so valid credentials from new providers are accepted.
    if not isinstance(value, str) or not value.strip():
        raise InvalidConfig(key, "Credential cannot be empty")


def validate_path(key: str, value: str) -> None:
    """Validate path syntax without requiring the process CWD to contain its parent."""
    if not value:
        raise InvalidConfig(key, "Path cannot be empty")
    path = Path(value)
    if path.is_absolute() and not path.parent.exists():
        raise InvalidConfig(key, f"Parent directory does not exist: {path.parent}")


def validate_log_level(key: str, value: str) -> None:
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if not isinstance(value, str) or value.upper() not in valid_levels:
        raise InvalidConfig(key, f"Must be one of: {', '.join(sorted(valid_levels))}")


def validate_bool(key: str, value: Any) -> None:
    valid_values = {True, False, "true", "false", "1", "0", "yes", "no"}
    if value not in valid_values:
        raise InvalidConfig(key, "Must be a boolean value")


def validate_number(key: str, value: Any, min_val: float = None, max_val: float = None) -> None:
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise InvalidConfig(key, f"Must be a number, got: {type(value).__name__}")
    if not math.isfinite(num):
        raise InvalidConfig(key, "Must be a finite number")
    if min_val is not None and num < min_val:
        raise InvalidConfig(key, f"Must be >= {min_val}, got: {num}")
    if max_val is not None and num > max_val:
        raise InvalidConfig(key, f"Must be <= {max_val}, got: {num}")


def validate_config_value(key: str, value: Any, validator_name: str) -> None:
    validators = {
        "not_empty": validate_not_empty,
        "api_key": validate_api_key,
        "path": validate_path,
        "log_level": validate_log_level,
        "bool": validate_bool,
        "number": validate_number,
    }
    validator = validators.get(validator_name)
    if validator is not None:
        validator(key, value)
