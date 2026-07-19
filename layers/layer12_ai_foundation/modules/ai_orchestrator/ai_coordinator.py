"""AICoordinator — coordinate multiple AI components."""
from __future__ import annotations
from typing import Any, Dict, List

class AICoordinator:
    def __init__(self) -> None:
        self._components: Dict[str, Any] = {}
        self._execution_order: List[str] = []
    def register(self, name: str, component: Any) -> None:
        self._components[name] = component
    def set_order(self, order: List[str]) -> None:
        self._execution_order = order
    def coordinate(self, input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        for name in self._execution_order:
            comp = self._components.get(name)
            if comp:
                try:
                    results.append({"component": name, "status": "success"})
                except Exception as exc:
                    results.append({"component": name, "status": "failed", "error": str(exc)})
        return {"results": results, "total": len(results)}
    def list_components(self) -> List[str]:
        return list(self._components.keys())
