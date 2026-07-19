"""AIContext — context management for orchestrator."""
from __future__ import annotations
from typing import Any, Dict

class AIContext:
    def __init__(self) -> None:
        self._ctx: Dict[str, Any] = {}
    def set(self, key: str, value: Any) -> None: self._ctx[key] = value
    def get(self, key: str, default: Any = None) -> Any: return self._ctx.get(key, default)
    def merge(self, ctx: Dict[str, Any]) -> None: self._ctx.update(ctx)
    def keys(self) -> list: return list(self._ctx.keys())
    def clear(self) -> None: self._ctx.clear()
