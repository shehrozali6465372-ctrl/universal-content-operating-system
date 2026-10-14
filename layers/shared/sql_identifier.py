"""Shared validation for SQL identifiers used in multiple persistence backends."""
from __future__ import annotations

import re


class SQLIdentifierMixin:
    """Allow safe unquoted SQL identifiers while values remain parameterized."""

    _IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    @classmethod
    def _identifier(cls, value: str) -> str:
        if not isinstance(value, str) or not cls._IDENT.fullmatch(value):
            raise ValueError(f"unsafe SQL identifier: {value}")
        return value
