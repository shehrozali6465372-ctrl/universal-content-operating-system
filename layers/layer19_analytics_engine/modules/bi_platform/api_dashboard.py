"""APIDashboard — REST API endpoints and dashboard data serving."""
from __future__ import annotations
import json
import threading
import time
from typing import Any, Dict, List, Optional


class APIEndpoint:
    __slots__ = ("path", "method", "description", "handler", "rate_limit",
                 "auth_required", "calls_count", "avg_latency_ms", "last_called")

    def __init__(self, path: str, method: str = "GET", description: str = "") -> None:
        self.path = path
        self.method = method
        self.description = description
        self.handler = ""
        self.rate_limit = 100
        self.auth_required = True
        self.calls_count = 0
        self.avg_latency_ms = 0.0
        self.last_called = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path, "method": self.method,
            "description": self.description,
            "rate_limit": self.rate_limit,
            "auth_required": self.auth_required,
            "calls": self.calls_count,
            "avg_latency": round(self.avg_latency_ms, 2),
        }


class APIDashboard:
    """Manages REST API endpoints and serves dashboard data."""
    _instance: Optional["APIDashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "APIDashboard":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._endpoints: Dict[str, APIEndpoint] = {}
        self._method_index: Dict[str, List[str]] = {}
        self._request_log: List[Dict[str, Any]] = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        endpoints = [
            ("/api/v1/status", "GET", "System status"),
            ("/api/v1/ceo", "GET", "CEO dashboard"),
            ("/api/v1/revenue", "GET", "Revenue analytics"),
            ("/api/v1/niches", "GET", "Niche dashboard"),
            ("/api/v1/platforms", "GET", "Platform dashboard"),
            ("/api/v1/ai", "GET", "AI dashboard"),
            ("/api/v1/empire", "GET", "Empire dashboard"),
            ("/api/v1/alerts", "GET", "Active alerts"),
            ("/api/v1/forecast", "GET", "Revenue forecast"),
            ("/api/v1/reports", "GET", "Executive reports"),
            ("/api/v1/health", "GET", "Health check"),
        ]
        for path, method, desc in endpoints:
            ep = APIEndpoint(path, method, desc)
            self._endpoints[path] = ep
            self._method_index.setdefault(method, []).append(path)

    def register_endpoint(self, path: str, method: str = "GET",
                          description: str = "", rate_limit: int = 100) -> APIEndpoint:
        ep = APIEndpoint(path, method, description)
        ep.rate_limit = rate_limit
        self._endpoints[path] = ep
        self._method_index.setdefault(method, []).append(path)
        return ep

    def log_request(self, path: str, method: str = "GET",
                    latency_ms: float = 0.0, status: int = 200) -> None:
        ep = self._endpoints.get(path)
        if ep:
            ep.calls_count += 1
            n = ep.calls_count
            ep.avg_latency_ms = ((ep.avg_latency_ms * (n - 1) + latency_ms) / n)
            ep.last_called = time.time()
        self._request_log.append({
            "path": path, "method": method,
            "latency_ms": latency_ms, "status": status,
            "timestamp": time.time(),
        })

    def get_endpoint(self, path: str) -> Optional[APIEndpoint]:
        return self._endpoints.get(path)

    def get_all_endpoints(self) -> List[APIEndpoint]:
        return list(self._endpoints.values())

    def get_api_status(self) -> Dict[str, Any]:
        endpoints = list(self._endpoints.values())
        return {
            "total_endpoints": len(endpoints),
            "total_requests": sum(e.calls_count for e in endpoints),
            "avg_latency": round(
                sum(e.avg_latency_ms for e in endpoints) / len(endpoints), 2
            ) if endpoints else 0,
            "by_method": {m: len(paths) for m, paths in self._method_index.items()},
            "endpoints": [e.to_dict() for e in endpoints],
        }

    def get_request_stats(self) -> Dict[str, Any]:
        logs = self._request_log[-1000:]
        return {
            "total_requests": len(self._request_log),
            "recent_requests": len(logs),
            "avg_latency": round(
                sum(l["latency_ms"] for l in logs) / len(logs), 2
            ) if logs else 0,
            "error_rate": round(
                sum(1 for l in logs if l["status"] >= 400) / len(logs) * 100, 1
            ) if logs else 0,
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "endpoints": len(self._endpoints),
            "requests": len(self._request_log),
        }


def get_api_dashboard() -> APIDashboard:
    return APIDashboard()
