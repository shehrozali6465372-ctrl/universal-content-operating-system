"""persistence_validator.py — Configuration and state validation."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.persistence_kernel.persistence_configuration import PersistenceConfiguration


class ValidationResult:
    """Result of a validation."""
    __slots__ = ("valid", "errors", "warnings")

    def __init__(self) -> None:
        self.valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "errors": self.errors, "warnings": self.warnings}


class PersistenceValidator:
    """Validates persistence configuration and state."""

    def __init__(self) -> None:
        self._rules: List[Dict[str, Any]] = []

    def validate_config(self, config: PersistenceConfiguration) -> ValidationResult:
        result = ValidationResult()
        if not config.database_url:
            result.add_error("database_url is required")
        if config.pool_size < 1:
            result.add_error("pool_size must be >= 1")
        if config.pool_timeout < 1:
            result.add_warning("pool_timeout is very low")
        if config.cache_ttl < 0:
            result.add_error("cache_ttl must be >= 0")
        for rule in self._rules:
            check = rule.get("check")
            if check and not check(config):
                result.add_error(rule.get("message", "Validation failed"))
        return result

    def add_rule(self, name: str, check: Callable, message: str = "") -> None:
        self._rules.append({"name": name, "check": check, "message": message})

    def validate_state(self, state: str, valid_states: List[str]) -> ValidationResult:
        result = ValidationResult()
        if state not in valid_states:
            result.add_error(f"Invalid state: {state}. Valid: {valid_states}")
        return result
