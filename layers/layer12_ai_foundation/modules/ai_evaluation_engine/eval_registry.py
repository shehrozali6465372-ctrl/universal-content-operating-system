"""EvalRegistry — register and manage evaluation components."""
from __future__ import annotations
from typing import Any, Dict, Optional

class EvalRegistry:
    def __init__(self) -> None:
        self._components: Dict[str, Any] = {}
    def register(self, name: str, component: Any) -> None: self._components[name] = component
    def unregister(self, name: str) -> bool: return self._components.pop(name, None) is not None
    def get(self, name: str) -> Optional[Any]: return self._components.get(name)
    def list_components(self) -> list: return list(self._components.keys())
    def count(self) -> int: return len(self._components)
