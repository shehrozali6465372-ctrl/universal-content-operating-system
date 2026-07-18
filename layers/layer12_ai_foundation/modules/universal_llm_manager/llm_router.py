"""LLMRouter — Route requests to appropriate providers."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

class LLMRouter:
    def __init__(self) -> None:
        self._routes: Dict[str, str] = {}
        self._priority: List[str] = []
    def add_route(self, task_type: str, provider: str, priority: int = 0) -> None:
        self._routes[task_type] = provider
        if provider not in self._priority:
            self._priority.append(provider)
    def route(self, task_type: str) -> str:
        return self._routes.get(task_type, self._priority[0] if self._priority else "openai")
    def get_all_routes(self) -> Dict[str, str]:
        return dict(self._routes)
    def get_stats(self) -> Dict[str, Any]:
        return {"routes": len(self._routes), "providers": len(self._priority)}
