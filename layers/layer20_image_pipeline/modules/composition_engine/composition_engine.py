"""CompositionEngine — image composition and layout planning."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class CompositionRule:
    __slots__ = ("name", "description", "check_fn", "metadata")

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.check_fn = None
        self.metadata: Dict[str, Any] = {}


class CompositionPlan:
    __slots__ = ("plan_id", "layout", "elements", "dimensions", "metadata")

    def __init__(self, layout: str = "center", dimensions: tuple = (1080, 1080)) -> None:
        self.plan_id = f"comp_{id(self) % 100000}"
        self.layout = layout
        self.elements: List[Dict[str, Any]] = []
        self.dimensions = dimensions
        self.metadata: Dict[str, Any] = {}

    def add_element(self, element_type: str, position: tuple = (0, 0),
                    size: tuple = (100, 100)) -> None:
        self.elements.append({"type": element_type, "position": position, "size": size})

    def to_dict(self) -> Dict[str, Any]:
        return {"plan_id": self.plan_id, "layout": self.layout,
                "dimensions": self.dimensions, "elements": len(self.elements)}


class CompositionEngine:
    def __init__(self) -> None:
        self._rules: List[CompositionRule] = []
        self._layouts: Dict[str, Dict[str, Any]] = {
            "center": {"alignment": "center", "spacing": 0},
            "grid": {"columns": 3, "gutter": 10},
            "masonry": {"columns": 2, "gutter": 5},
            "stack": {"direction": "vertical", "spacing": 20},
        }

    def create_plan(self, layout: str = "center",
                    dimensions: tuple = (1080, 1080)) -> CompositionPlan:
        plan = CompositionPlan(layout, dimensions)
        if layout in self._layouts:
            plan.metadata["layout_config"] = self._layouts[layout]
        return plan

    def add_layout(self, name: str, config: Dict[str, Any]) -> None:
        self._layouts[name] = config

    def add_rule(self, rule: CompositionRule) -> None:
        self._rules.append(rule)

    def validate(self, plan: CompositionPlan) -> Dict[str, Any]:
        violations = []
        for rule in self._rules:
            if rule.check_fn and not rule.check_fn(plan):
                violations.append(rule.name)
        return {"valid": len(violations) == 0, "violations": violations}

    def list_layouts(self) -> List[str]:
        return list(self._layouts.keys())
