"""Production-safe API documentation generation."""

from __future__ import annotations

from copy import deepcopy
import re
from threading import RLock
from typing import Any, Dict, List, Optional


_HTTP_METHODS = frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"})
_PATH_RE = re.compile(r"^/[A-Za-z0-9_./:{}?=&%+\-]*$")


class APIDocumentation:
    """Build deterministic API documentation with validated, isolated state."""

    def __init__(self, title: str = "AIOS API", version: str = "4.0.0") -> None:
        self.title = self._require_text(title, "title")
        self.version = self._require_text(version, "version")
        self._lock = RLock()
        self._endpoints: List[Dict[str, Any]] = []

    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-blank string")
        return value.strip()

    @staticmethod
    def _validate_endpoint_path(path: str) -> str:
        path = APIDocumentation._require_text(path, "path")
        if not _PATH_RE.fullmatch(path):
            raise ValueError("path must start with '/' and contain only safe URL path characters")
        return path

    def add_endpoint(
        self,
        method: str,
        path: str,
        description: str = "",
        parameters: Optional[List[Dict[str, Any]]] = None,
        response_example: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add one unique endpoint while preventing caller mutation."""
        if not isinstance(method, str) or not method.strip():
            raise ValueError("method must be a non-blank string")
        normalized_method = method.strip().upper()
        if normalized_method not in _HTTP_METHODS:
            raise ValueError(f"unsupported HTTP method: {normalized_method}")
        normalized_path = self._validate_endpoint_path(path)
        if not isinstance(description, str):
            raise TypeError("description must be a string")
        if parameters is not None and (
            not isinstance(parameters, list)
            or not all(isinstance(item, dict) for item in parameters)
        ):
            raise TypeError("parameters must be a list of dictionaries")
        if response_example is not None and not isinstance(response_example, dict):
            raise TypeError("response_example must be a dictionary")

        endpoint = {
            "method": normalized_method,
            "path": normalized_path,
            "description": description.strip(),
            "parameters": deepcopy(parameters) if parameters is not None else [],
            "response_example": deepcopy(response_example) if response_example is not None else {},
        }
        with self._lock:
            key = (normalized_method, normalized_path)
            if any((item["method"], item["path"]) == key for item in self._endpoints):
                raise ValueError(f"duplicate endpoint: {normalized_method} {normalized_path}")
            self._endpoints.append(endpoint)

    def generate(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "title": self.title,
                "version": self.version,
                "endpoints": deepcopy(self._endpoints),
                "total_endpoints": len(self._endpoints),
            }

    def generate_markdown(self) -> str:
        with self._lock:
            endpoints = deepcopy(self._endpoints)
            title = self.title
            version = self.version
        lines = [f"# {title} v{version}", ""]
        for endpoint in endpoints:
            lines.extend(
                [
                    f"## {endpoint['method']} {endpoint['path']}",
                    endpoint["description"],
                    "",
                ]
            )
        return "\n".join(lines)

    def list_endpoints(self) -> List[Dict[str, Any]]:
        with self._lock:
            return deepcopy(self._endpoints)
