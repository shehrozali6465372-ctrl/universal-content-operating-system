"""AIGateway — universal API gateway for AI operations."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class AIGateway:
    """Gateway with explicit validation and stable failure contracts."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._request_count = 0

    def register_handler(
        self, endpoint: str, handler: Callable[[Dict[str, Any]], Any]
    ) -> None:
        endpoint = endpoint.strip()
        if not endpoint:
            raise ValueError("endpoint must not be empty")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handlers[endpoint] = handler

    def handle(
        self, endpoint: str, data: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        self._request_count += 1
        endpoint = endpoint.strip()
        if not endpoint:
            return {"success": False, "error": "endpoint must not be empty",
                    "error_code": "INVALID_ENDPOINT"}

        handler = self._handlers.get(endpoint)
        if handler is None:
            return {"success": False, "error": f"No handler for {endpoint}",
                    "error_code": "HANDLER_NOT_FOUND"}

        payload = {} if data is None else data
        if not isinstance(payload, dict):
            return {"success": False, "error": "request data must be a dictionary",
                    "error_code": "INVALID_PAYLOAD"}

        try:
            result = handler(payload)
        except Exception:
            logger.exception("AI gateway handler failed for endpoint=%s", endpoint)
            return {"success": False, "error": "AI handler execution failed",
                    "error_code": "HANDLER_ERROR"}

        return {"success": True, "result": result}

    def list_endpoints(self) -> List[str]:
        return sorted(self._handlers)

    def request_count(self) -> int:
        return self._request_count
