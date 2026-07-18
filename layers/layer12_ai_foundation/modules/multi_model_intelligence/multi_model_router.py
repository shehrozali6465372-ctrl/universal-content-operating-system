"""MultiModelRouter — route requests to appropriate model combinations."""
from __future__ import annotations

from typing import Dict, List, Optional


class MultiModelRouter:
    """Route multi-model requests based on task type and requirements."""

    TASK_MODEL_MAP: Dict[str, List[str]] = {
        "generation": ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"],
        "reasoning": ["gpt-4o", "claude-sonnet-4-20250514"],
        "creative": ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"],
        "analysis": ["gpt-4o", "claude-sonnet-4-20250514"],
        "coding": ["gpt-4o", "claude-sonnet-4-20250514"],
        "review": ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"],
    }

    def __init__(self) -> None:
        self._custom_routes: Dict[str, List[str]] = {}

    def route(self, task_type: str, prompt: str = "",
              models: Optional[List[str]] = None) -> List[str]:
        if models:
            return models
        if task_type in self._custom_routes:
            return self._custom_routes[task_type]
        return self.TASK_MODEL_MAP.get(task_type, ["gpt-4o"])

    def register_route(self, task_type: str, models: List[str]) -> None:
        self._custom_routes[task_type] = models

    def unregister_route(self, task_type: str) -> bool:
        if task_type in self._custom_routes:
            del self._custom_routes[task_type]
            return True
        return False

    def get_all_routes(self) -> Dict[str, List[str]]:
        all_routes = dict(self.TASK_MODEL_MAP)
        all_routes.update(self._custom_routes)
        return all_routes
