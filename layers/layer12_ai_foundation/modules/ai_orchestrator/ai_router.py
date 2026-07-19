"""AIRouter — route AI requests to appropriate components."""
from __future__ import annotations
from typing import Dict

class AIRouter:
    TASK_ROUTES: Dict[str, str] = {
        "generate": "llm_manager", "chat": "llm_manager", "write": "prompt",
        "analyze": "reasoning", "optimize": "cost", "evaluate": "evaluation",
        "govern": "governance", "remember": "memory", "research": "research",
    }
    def __init__(self) -> None:
        self._custom_routes: Dict[str, str] = {}
    def route(self, task_type: str) -> str:
        return self._custom_routes.get(task_type, self.TASK_ROUTES.get(task_type, "llm_manager"))
    def register(self, task_type: str, target: str) -> None:
        self._custom_routes[task_type] = target
    def list_routes(self) -> Dict[str, str]:
        routes = dict(self.TASK_ROUTES); routes.update(self._custom_routes); return routes
