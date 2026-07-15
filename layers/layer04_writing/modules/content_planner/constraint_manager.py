"""Constraint Manager — Manage writing constraints and requirements."""
from __future__ import annotations
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

    def add(self, name: str, constraint_type: str = "must",
            value: Any = None, description: str = "") -> WritingConstraint:
        """Add a constraint."""
        c = WritingConstraint(name=name, constraint_type=constraint_type, value=value)
        c.description = description
        self._constraints[name] = c
        return c

    def remove(self, name: str) -> bool:
        return self._constraints.pop(name, None) is not None

    def get(self, name: str) -> Optional[WritingConstraint]:
        return self._constraints.get(name)

    def check(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check plan data against all constraints."""
        violations: List[Dict[str, Any]] = []
        for name, constraint in self._constraints.items():
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
        return list(self._constraints.values())

    def count(self) -> int:
        return len(self._constraints)

    def clear(self) -> None:
        self._constraints.clear()
