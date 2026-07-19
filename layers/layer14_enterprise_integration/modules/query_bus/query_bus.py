"""QueryBus — dispatch read-only queries to registered handlers."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


class Query:
    __slots__ = ("query_id", "name", "params", "source", "timestamp")

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None,
                 source: str = "") -> None:
        self.query_id = str(uuid.uuid4())[:12]
        self.name = name
        self.params = params or {}
        self.source = source
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"query_id": self.query_id, "name": self.name,
                "params": self.params, "source": self.source}


class QueryResult:
    __slots__ = ("query_id", "success", "data", "error", "duration_ms")

    def __init__(self, query_id: str) -> None:
        self.query_id = query_id
        self.success = False
        self.data: Any = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"query_id": self.query_id, "success": self.success,
                "error": self.error, "duration_ms": round(self.duration_ms, 2)}


class QueryBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, query_name: str, handler: Callable) -> None:
        self._handlers[query_name] = handler

    def unregister(self, query_name: str) -> bool:
        if query_name in self._handlers:
            del self._handlers[query_name]
            return True
        return False

    def execute(self, name: str, params: Optional[Dict[str, Any]] = None,
                source: str = "") -> QueryResult:
        q = Query(name, params, source)
        result = QueryResult(q.query_id)
        handler = self._handlers.get(name)
        if not handler:
            result.error = "no_handler_registered"
            self._history.append({**q.to_dict(), "result": result.to_dict()})
            return result
        start = time.time()
        try:
            result.data = handler(q.params)
            result.success = True
        except Exception as exc:
            result.error = str(exc)
        result.duration_ms = (time.time() - start) * 1000
        self._history.append({**q.to_dict(), "result": result.to_dict()})
        return result

    def list_queries(self) -> List[str]:
        return list(self._handlers.keys())

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
