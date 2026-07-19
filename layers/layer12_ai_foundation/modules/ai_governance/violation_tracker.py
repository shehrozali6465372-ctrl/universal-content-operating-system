"""ViolationTracker — track all policy violations."""
from __future__ import annotations
from typing import List
from .models import Violation

class ViolationTracker:
    def __init__(self) -> None:
        self._violations: List[Violation] = []
    def track(self, violation: Violation) -> None:
        self._violations.append(violation)
    def get_all(self) -> List[Violation]:
        return list(self._violations)
    def get_by_type(self, policy_type: str) -> List[Violation]:
        return [v for v in self._violations if v.policy_type == policy_type]
    def get_by_severity(self, severity: str) -> List[Violation]:
        return [v for v in self._violations if v.severity == severity]
    def count(self) -> int:
        return len(self._violations)
    def count_critical(self) -> int:
        return len([v for v in self._violations if v.severity == "critical"])
    def clear(self) -> None:
        self._violations.clear()
