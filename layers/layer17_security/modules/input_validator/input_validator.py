"""InputValidator — validate and sanitize all user inputs."""
from __future__ import annotations
import re
from typing import Any, Callable, Dict, List, Optional


class ValidationRule:
    __slots__ = ("name", "check_fn", "message", "severity")

    def __init__(self, name: str, check_fn: Callable, message: str = "",
                 severity: str = "error") -> None:
        self.name = name
        self.check_fn = check_fn
        self.message = message
        self.severity = severity


class InputValidator:
    def __init__(self) -> None:
        self._rules: Dict[str, List[ValidationRule]] = {}
        self._errors: List[str] = []

    def add_rule(self, field: str, rule: ValidationRule) -> None:
        self._rules.setdefault(field, []).append(rule)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        for field, rules in self._rules.items():
            value = data.get(field)
            for rule in rules:
                try:
                    if not rule.check_fn(value):
                        errors.append(f"{field}: {rule.message or rule.name}")
                except Exception as exc:
                    errors.append(f"{field}: {str(exc)}")
        self._errors.extend(errors)
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_field(self, field: str, value: Any) -> Dict[str, Any]:
        errors = []
        for rule in self._rules.get(field, []):
            try:
                if not rule.check_fn(value):
                    errors.append(rule.message or rule.name)
            except Exception as exc:
                errors.append(str(exc))
        return {"valid": len(errors) == 0, "errors": errors}

    def is_valid_email(self, email: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    def is_valid_url(self, url: str) -> bool:
        return bool(re.match(r'^https?://', url))

    def sanitize_string(self, value: str, max_length: int = 1000) -> str:
        value = value.strip()
        value = re.sub(r'<[^>]+>', '', value)
        value = value[:max_length]
        return value

    def get_errors(self) -> List[str]:
        return list(self._errors)

    def clear_errors(self) -> None:
        self._errors.clear()
