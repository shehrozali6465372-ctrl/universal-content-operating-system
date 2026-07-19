"""ResponseRouter — aggregate and route responses from multiple layers."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class ResponseEnvelope:
    __slots__ = ("source", "data", "status", "timestamp", "latency_ms", "metadata")

    def __init__(self, source: str, data: Any = None, status: str = "ok") -> None:
        self.source = source
        self.data = data
        self.status = status
        self.timestamp = time.time()
        self.latency_ms: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "status": self.status,
                "latency_ms": round(self.latency_ms, 2)}


class ResponseRouter:
    def __init__(self) -> None:
        self._routes: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def add_route(self, source: str, handler: Callable) -> None:
        self._routes[source] = handler

    def remove_route(self, source: str) -> bool:
        if source in self._routes:
            del self._routes[source]
            return True
        return False

    def route(self, source: str, data: Any = None) -> ResponseEnvelope:
        envelope = ResponseEnvelope(source, data)
        handler = self._routes.get(source)
        if not handler:
            envelope.status = "no_route"
            self._history.append(envelope.to_dict())
            return envelope
        start = time.time()
        try:
            envelope.data = handler(data)
            envelope.status = "ok"
        except Exception as exc:
            envelope.status = "error"
            envelope.metadata["error"] = str(exc)
        envelope.latency_ms = (time.time() - start) * 1000
        self._history.append(envelope.to_dict())
        return envelope

    def route_all(self, requests: Dict[str, Any]) -> Dict[str, ResponseEnvelope]:
        results = {}
        for source, data in requests.items():
            results[source] = self.route(source, data)
        return results

    def aggregate(self, responses: List[ResponseEnvelope]) -> Dict[str, Any]:
        ok = [r for r in responses if r.status == "ok"]
        failed = [r for r in responses if r.status != "ok"]
        return {"total": len(responses), "success": len(ok),
                "failed": len(failed), "sources": [r.source for r in ok]}

    def list_routes(self) -> List[str]:
        return list(self._routes.keys())

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
