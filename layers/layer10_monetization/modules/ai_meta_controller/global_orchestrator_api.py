"""Global Orchestrator API — Universal interface for all layers."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

_GO_COUNTER = itertools.count(1)


class GlobalOrchestratorAPI:
    """Universal interface providing execute/analyze/publish/learn/optimize."""

    def __init__(self) -> None:
        self.api_id: str = f"api_{next(_GO_COUNTER)}"
        self._handlers: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []
        self._active: bool = False

    def register(self, operation: str, handler: Callable) -> None:
        self._handlers[operation] = handler

    def execute(self, operation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        handler = self._handlers.get(operation)
        start = time.time()
        if handler:
            try:
                result = handler(context or {})
                self._history.append({"operation": operation, "status": "success",
                                       "duration_ms": (time.time() - start) * 1000})
                return {"status": "success", "result": result}
            except Exception as e:
                self._history.append({"operation": operation, "status": "error",
                                       "error": str(e)})
                return {"status": "error", "error": str(e)}
        return {"status": "not_found", "operation": operation}

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute("analyze", context)

    def publish(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute("publish", context)

    def learn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute("learn", context)

    def optimize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute("optimize", context)

    def rollback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute("rollback", context)

    def recover(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute("recover", context)

    def shutdown(self) -> Dict[str, Any]:
        self._active = False
        return {"status": "shutdown", "total_operations": len(self._history)}

    def status(self) -> Dict[str, Any]:
        return {
            "api_id": self.api_id, "active": self._active,
            "handlers": len(self._handlers), "history": len(self._history),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._history[-limit:]
