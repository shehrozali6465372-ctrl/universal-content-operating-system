"""APIGateway — bounded, rate-limited request dispatch with middleware."""
from __future__ import annotations

import itertools
import threading
import time
from typing import Any, Callable, Dict, List, Optional

_AG_COUNTER = itertools.count(1)


class APIRequest:
    """An API request."""

    __slots__ = ("request_id", "endpoint", "method", "body", "params", "created_at")

    def __init__(self, endpoint: str = "", method: str = "POST") -> None:
        self.request_id = f"req_{next(_AG_COUNTER)}"
        self.endpoint = endpoint
        self.method = method
        self.body: Dict[str, Any] = {}
        self.params: Dict[str, Any] = {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "body": dict(self.body),
            "params": dict(self.params),
            "created_at": self.created_at,
        }


class APIResponse:
    """An API response."""

    __slots__ = ("status_code", "data", "error", "latency_ms")

    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.data: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.latency_ms = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "status_code": self.status_code,
            "data": self.data,
            "latency_ms": round(self.latency_ms, 2),
        }
        if self.error:
            result["error"] = self.error
        return result


class APIGateway:
    """Universal API gateway with bounded history and rate limiting."""

    def __init__(
        self,
        rate_limit: int = 1000,
        window_seconds: int = 60,
        max_history: int = 10000,
        max_clients: int = 10000,
    ) -> None:
        if rate_limit <= 0 or window_seconds <= 0:
            raise ValueError("rate_limit and window_seconds must be positive")
        if max_history <= 0 or max_clients <= 0:
            raise ValueError("max_history and max_clients must be positive")
        self._handlers: Dict[str, Callable[[APIRequest], Any]] = {}
        self._requests: List[APIRequest] = []
        self._middleware: List[
            Callable[[APIRequest], Optional[APIResponse]]
        ] = []
        self._rate_limit = rate_limit
        self._window_seconds = window_seconds
        self._request_times: Dict[str, List[float]] = {}
        self._request_count = 0
        self._max_history = max_history
        self._max_clients = max_clients
        self._lock = threading.RLock()

    def register_handler(
        self, endpoint: str, handler: Callable[[APIRequest], Any]
    ) -> None:
        if not endpoint or not callable(handler):
            raise ValueError("endpoint and callable handler are required")
        with self._lock:
            self._handlers[endpoint] = handler

    def add_middleware(
        self, middleware: Callable[[APIRequest], Optional[APIResponse]]
    ) -> None:
        if not callable(middleware):
            raise ValueError("middleware must be callable")
        with self._lock:
            self._middleware.append(middleware)

    def handle(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        client_id: str = "anonymous",
    ) -> APIResponse:
        start = time.time()
        request = APIRequest(endpoint)
        request.body = dict(body or {})
        request.params = dict(params or {})

        with self._lock:
            self._requests.append(request)
            if len(self._requests) > self._max_history:
                del self._requests[:-self._max_history]
            self._request_count += 1

            response = APIResponse()
            now = time.time()
            times = [
                t
                for t in self._request_times.get(client_id, [])
                if now - t < self._window_seconds
            ]

            if len(times) >= self._rate_limit:
                self._request_times[client_id] = times
                response.status_code = 429
                response.error = "Rate limit exceeded"
                response.latency_ms = (time.time() - start) * 1000
                return response

            if (
                client_id not in self._request_times
                and len(self._request_times) >= self._max_clients
            ):
                response.status_code = 429
                response.error = "Client limit exceeded"
                response.latency_ms = (time.time() - start) * 1000
                return response

            times.append(now)
            self._request_times[client_id] = times

            try:
                for middleware in list(self._middleware):
                    middleware_response = middleware(request)
                    if middleware_response is not None:
                        response = middleware_response
                        return response

                handler = self._handlers.get(endpoint)
                if handler is None:
                    response.status_code = 404
                    response.error = f"Endpoint '{endpoint}' not found"
                else:
                    result = handler(request)
                    response.data = (
                        result if isinstance(result, dict) else {"result": result}
                    )
            except Exception:
                response.status_code = 500
                response.error = "Internal server error"
            finally:
                response.latency_ms = (time.time() - start) * 1000
            return response

    def get_endpoints(self) -> List[str]:
        with self._lock:
            return list(self._handlers)

    def get_requests(self, count: int = 10) -> List[Dict[str, Any]]:
        if count <= 0:
            return []
        with self._lock:
            return [request.to_dict() for request in self._requests[-count:]]

    def set_rate_limit(self, limit: int) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            self._rate_limit = limit

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            endpoints: Dict[str, int] = {}
            for request in self._requests:
                endpoints[request.endpoint] = endpoints.get(request.endpoint, 0) + 1
            return {
                "total_requests": self._request_count,
                "retained_requests": len(self._requests),
                "registered_endpoints": len(self._handlers),
                "tracked_clients": len(self._request_times),
                "by_endpoint": endpoints,
                "rate_limit": self._rate_limit,
                "window_seconds": self._window_seconds,
            }
