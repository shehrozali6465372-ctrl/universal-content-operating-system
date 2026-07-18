"""RuntimeValidator — Validate runtime configuration and state."""
from __future__ import annotations
from typing import Any, Dict, List


class ValidationResult:
    """Result of a validation check."""
    __slots__ = ("is_valid", "errors", "warnings")

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        return {"is_valid": self.is_valid, "errors": self.errors, "warnings": self.warnings}


class RuntimeValidator:
    """Validate runtime configuration and state."""

    def __init__(self) -> None:
        self._validations: List[ValidationResult] = []

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        if config.get("max_workers", 0) < 1:
            result.add_error("max_workers must be >= 1")
        if config.get("task_timeout", 0) <= 0:
            result.add_error("task_timeout must be > 0")
        if config.get("max_tasks", 0) < 1:
            result.add_error("max_tasks must be >= 1")
        if config.get("max_retries", 0) < 0:
            result.add_warning("max_retries is negative")
        self._validations.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        valid = sum(1 for v in self._validations if v.is_valid)
        return {"total": len(self._validations), "valid": valid,
                "invalid": len(self._validations) - valid}
