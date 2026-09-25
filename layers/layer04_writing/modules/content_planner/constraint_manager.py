"""Constraint Manager — Manage writing constraints and requirements."""
from __future__ import annotations
from threading import RLock
from typing import Any, Dict, List, Optional


class WritingConstraint:
    """A single writing constraint."""
    __slots__ = ("name", "constraint_type", "value", "severity", "description")

    def __init__(self, name: str = "", constraint_type: str = "must",
                 value: Any = None) -> None:
        self.name = name
        self.constraint_type = constraint_type  # must, should, prefer
        self.value = value
        self.severity = "medium"
        self.description = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.constraint_type,
            "value": self.value,
            "severity": self.severity,
        }


class ConstraintManager:
    """Manages a set of writing constraints."""

    def __init__(self) -> None:
        self._constraints: Dict[str, WritingConstraint] = {}
        self._lock = RLock()

    def add(self, name: str, constraint_type: str = "must",
            value: Any = None, description: str = "") -> WritingConstraint:
        """Add a constraint."""
        c = WritingConstraint(name=name, constraint_type=constraint_type, value=value)
        c.description = description
        with self._lock:
            self._constraints[name] = c
        return c

    def remove(self, name: str) -> bool:
        with self._lock:
            return self._constraints.pop(name, None) is not None

    def get(self, name: str) -> Optional[WritingConstraint]:
        with self._lock:
            c = self._constraints.get(name)
            if c is None:
                return None
            return self._copy(c)

    def check(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check plan data against all constraints."""
        violations: List[Dict[str, Any]] = []
        with self._lock:
            constraints = {name: self._copy(c) for name, c in self._constraints.items()}
        for name, constraint in constraints.items():
            if constraint.constraint_type == "must":
                plan_value = plan_data.get(name)
                if plan_value != constraint.value:
                    violations.append({
                        "constraint": name,
                        "type": "must",
                        "expected": constraint.value,
                        "actual": plan_value,
                        "passed": False,
                    })
            elif constraint.constraint_type == "should":
                plan_value = plan_data.get(name)
                if plan_value is None:
                    violations.append({
                        "constraint": name,
                        "type": "should",
                        "expected": constraint.value,
                        "actual": None,
                        "passed": False,
                    })
        return violations

    def get_all(self) -> List[WritingConstraint]:
        with self._lock:
            return [self._copy(c) for c in self._constraints.values()]

    def count(self) -> int:
        with self._lock:
            return len(self._constraints)

    @staticmethod
    def _copy(constraint: WritingConstraint) -> WritingConstraint:
        c = WritingConstraint(constraint.name, constraint.constraint_type, constraint.value)
        c.severity = constraint.severity
        c.description = constraint.description
        return c

    def clear(self) -> None:
        with self._lock:
            self._constraints.clear()
