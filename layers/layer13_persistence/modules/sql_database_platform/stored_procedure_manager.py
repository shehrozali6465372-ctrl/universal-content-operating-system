"""stored_procedure_manager.py — Stored procedure management."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional


class StoredProcedure:
    """Stored procedure definition."""
    __slots__ = ("name", "parameters", "handler", "description")
    _counter = 0

    def __init__(self, name: str, handler: Callable = None) -> None:
        StoredProcedure._counter += 1
        self.name = name
        self.parameters: List[Dict[str, str]] = []
        self.handler = handler
        self.description: str = ""


class StoredProcedureManager:
    """Manages stored procedures."""

    def __init__(self) -> None:
        self._procedures: Dict[str, StoredProcedure] = {}
        self._execution_count: Dict[str, int] = {}

    def register(self, procedure: StoredProcedure) -> None:
        self._procedures[procedure.name] = procedure

    def call(self, name: str, params: Dict[str, Any] = None) -> Any:
        proc = self._procedures.get(name)
        if proc and proc.handler:
            self._execution_count[name] = self._execution_count.get(name, 0) + 1
            return proc.handler(params or {})
        return None

    def get(self, name: str) -> Optional[StoredProcedure]:
        return self._procedures.get(name)

    def list_all(self) -> List[StoredProcedure]:
        return list(self._procedures.values())

    def stats(self) -> Dict[str, Any]:
        return {"procedures": len(self._procedures),
                "total_executions": sum(self._execution_count.values())}
