"""CostContext — context management for cost operations."""
from __future__ import annotations
from typing import Any, Dict
class CostContext:
    def __init__(self) -> None:
        self._ctx: Dict[str, Any] = {}
    def set(self, key: str, value: Any) -> None:
        self._ctx[key] = value
    def get(self, key: str, default: Any = None) -> Any:
        return self._ctx.get(key, default)
    def clear(self) -> None:
        self._ctx.clear()
