"""Constraint Solver - Checks and enforces constraints on decisions."""
from __future__ import annotations
from typing import Callable, Dict, List


class Constraint:
    """A single constraint with check function."""
    __slots__ = ("name", "check_fn", "severity", "description", "enabled")

    def __init__(self, name: str, check_fn: Callable[[Dict], bool],
                 severity: str = "error", description: str = ""):
        self.name = name
        self.check_fn = check_fn
        self.severity = severity  # error, warning, info
        self.description = description
        self.enabled = True

    def check(self, context: Dict) -> bool:
        if not self.enabled:
            return True
        try:
            return self.check_fn(context)
        except Exception:
            return False


class ConstraintResult:
    """Result of constraint checking."""
    __slots__ = ("violations", "warnings", "passed", "total", "feasible")

    def __init__(self) -> None:
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
        self.total = 0
        self.feasible = True

    def to_dict(self) -> Dict:
        return {"violations": list(self.violations), "warnings": list(self.warnings),
                "passed_count": len(self.passed), "total": self.total, "feasible": self.feasible}


class ConstraintSolver:
    """Checks constraints against a context."""

    def __init__(self) -> None:
        self._constraints: List[Constraint] = []

    def add_constraint(self, constraint: Constraint) -> None:
        self._constraints.append(constraint)

    def add_simple(self, name: str, check_fn: Callable, severity: str = "error") -> None:
        self.add_constraint(Constraint(name, check_fn, severity))

    def check(self, context: Dict) -> ConstraintResult:
        result = ConstraintResult()
        result.total = len(self._constraints)
        for c in self._constraints:
            if c.check(context):
                result.passed.append(c.name)
            elif c.severity == "error":
                result.violations.append(c.name)
                result.feasible = False
            else:
                result.warnings.append(c.name)
        return result

    def count(self) -> int:
        return len(self._constraints)
