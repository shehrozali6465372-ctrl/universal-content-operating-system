"""connection_monitor.py — Connection monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ConnectionMonitor:
    """Monitors database connections."""

    def __init__(self) -> None:
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._events: List[Dict[str, Any]] = []

    def record_connect(self, name: str, latency_ms: float = 0.0) -> None:
        self._connections[name] = {"status": "connected", "latency_ms": latency_ms,
                                    "connected_at": time.time()}
        self._events.append({"event": "connect", "name": name, "time": time.time()})

    def record_disconnect(self, name: str) -> None:
        self._connections[name] = {"status": "disconnected"}
        self._events.append({"event": "disconnect", "name": name, "time": time.time()})

    def record_error(self, name: str, error: str) -> None:
        self._events.append({"event": "error", "name": name, "error": error,
                              "time": time.time()})

    def get_connection(self, name: str) -> Dict[str, Any]:
        return self._connections.get(name, {"status": "unknown"})

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._events[-limit:]

    def stats(self) -> Dict[str, Any]:
        connected = sum(1 for c in self._connections.values() if c.get("status") == "connected")
        return {"total_connections": len(self._connections), "connected": connected}
