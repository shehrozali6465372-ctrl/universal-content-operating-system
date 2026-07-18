"""file_validator.py — File validation."""
from __future__ import annotations
from typing import Any, Dict, List


class FileValidator:
    """Validates files before storage."""

    def __init__(self, max_size_bytes: int = 100 * 1024 * 1024) -> None:
        self._max_size = max_size_bytes
        self._allowed_types: List[str] = []
        self._blocked_types: List[str] = []

    def set_allowed_types(self, types: List[str]) -> None:
        self._allowed_types = types

    def set_blocked_types(self, types: List[str]) -> None:
        self._blocked_types = types

    def validate(self, filename: str, size_bytes: int,
                 content_type: str = "") -> Dict[str, Any]:
        errors = []
        if size_bytes > self._max_size:
            errors.append(f"File too large: {size_bytes} > {self._max_size}")
        if self._blocked_types and content_type in self._blocked_types:
            errors.append(f"Blocked content type: {content_type}")
        if self._allowed_types and content_type and content_type not in self._allowed_types:
            errors.append(f"Content type not allowed: {content_type}")
        return {"valid": len(errors) == 0, "errors": errors}

    def is_valid(self, filename: str, size_bytes: int,
                 content_type: str = "") -> bool:
        return self.validate(filename, size_bytes, content_type)["valid"]
