"""ReasoningRouter — route problems to the best reasoning strategy."""
from __future__ import annotations

from typing import Dict

from .models import ReasoningType


class ReasoningRouter:
    """Route problems to the best reasoning strategy."""

    TASK_TYPE_MAP: Dict[str, ReasoningType] = {
        "logic": ReasoningType.LOGICAL, "deduction": ReasoningType.LOGICAL,
        "analysis": ReasoningType.ANALYTICAL, "data": ReasoningType.ANALYTICAL,
        "creative": ReasoningType.CREATIVE, "brainstorm": ReasoningType.CREATIVE,
        "strategy": ReasoningType.STRATEGIC, "plan": ReasoningType.PLANNING,
        "decision": ReasoningType.DECISION, "verify": ReasoningType.VERIFICATION,
        "reflect": ReasoningType.REFLECTION, "what_if": ReasoningType.LOGICAL,
    }

    def __init__(self) -> None:
        self._custom_routes: Dict[str, ReasoningType] = {}

    def route(self, problem_type: str) -> ReasoningType:
        if problem_type in self._custom_routes:
            return self._custom_routes[problem_type]
        return self.TASK_TYPE_MAP.get(problem_type, ReasoningType.LOGICAL)

    def register_route(self, problem_type: str, reasoning_type: ReasoningType) -> None:
        self._custom_routes[problem_type] = reasoning_type

    def get_all_routes(self) -> Dict[str, str]:
        routes = {k: v.value for k, v in self.TASK_TYPE_MAP.items()}
        routes.update({k: v.value for k, v in self._custom_routes.items()})
        return routes
