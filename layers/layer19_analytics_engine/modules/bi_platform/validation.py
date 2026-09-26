"""Validation primitives for Layer 19 analytics inputs.

These helpers keep the analytics layer fail-closed on malformed numeric and
identifier inputs. They deliberately do not coerce untrusted values silently.
"""
from __future__ import annotations

import math
from datetime import date as date_type
from datetime import datetime
from typing import Any


def require_non_blank(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")
    return value.strip()


def require_finite_number(value: float, field: str, *, minimum: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    if minimum is not None and number < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return number


def require_non_negative_int(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def require_limit(value: int, field: str = "limit", maximum: int = 1000) -> int:
    require_non_negative_int(value, field)
    if value > maximum:
        raise ValueError(f"{field} must be <= {maximum}")
    return value


def require_unit_interval(value: float, field: str) -> float:
    number = require_finite_number(value, field)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def require_percentage(value: float, field: str) -> float:
    number = require_finite_number(value, field)
    if not 0.0 <= number <= 100.0:
        raise ValueError(f"{field} must be between 0 and 100")
    return number


def require_date(value: str, field: str = "date") -> str:
    text = require_non_blank(value, field)
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD") from exc
    return text


def today_iso() -> str:
    return date_type.today().isoformat()


def copy_public(value: Any) -> Any:
    """Return a detached copy for public API boundaries."""
    if isinstance(value, dict):
        return {key: copy_public(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_public(item) for item in value]
    if isinstance(value, tuple):
        return tuple(copy_public(item) for item in value)
    return value
