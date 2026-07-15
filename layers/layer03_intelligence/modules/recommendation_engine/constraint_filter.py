"""Constraint Filter - Filters candidates based on constraints."""
from __future__ import annotations
from typing import Any, Callable, Dict, List


class FilterConstraint:
    __slots__ = ("name", "check_fn", "description")
    def __init__(self, name: str, check_fn: Callable, description: str = ""):
        self.name = name
        self.check_fn = check_fn
        self.description = description


class FilterResult:
    __slots__ = ("passed", "filtered_out", "reasons")
    def __init__(self) -> None:
        self.passed: List[Any] = []
        self.filtered_out: List[Dict] = []
        self.reasons: Dict[str, str] = {}
    def to_dict(self) -> Dict:
        return {"passed_count": len(self.passed), "filtered_count": len(self.filtered_out)}


class ConstraintFilter:
    def __init__(self) -> None:
        self._constraints: List[FilterConstraint] = []

    def add_constraint(self, constraint: FilterConstraint) -> None:
        self._constraints.append(constraint)

    def add_simple(self, name: str, check_fn: Callable) -> None:
        self._constraints.append(FilterConstraint(name, check_fn))

    def filter(self, candidates: List[Any]) -> FilterResult:
        result = FilterResult()
        for c in candidates:
            passed = True
            for constraint in self._constraints:
                try:
                    if not constraint.check_fn(c):
                        passed = False
                        result.reasons[c.topic] = constraint.name
                        break
                except Exception:
                    pass
            if passed:
                result.passed.append(c)
            else:
                result.filtered_out.append({"topic": c.topic, "reason": result.reasons.get(c.topic, "")})
        return result

    def count(self) -> int:
        return len(self._constraints)
