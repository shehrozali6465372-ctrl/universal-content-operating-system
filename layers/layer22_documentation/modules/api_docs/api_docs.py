"""APIDocs — auto-generate API documentation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class APIDocumentation:
    def __init__(self, title: str = "AIOS API", version: str = "4.0.0") -> None:
        self.title = title
        self.version = version
        self.endpoints: List[Dict[str, Any]] = []

    def add_endpoint(self, method: str, path: str, description: str = "",
                     parameters: Optional[List[Dict[str, Any]]] = None,
                     response_example: Optional[Dict[str, Any]] = None) -> None:
        self.endpoints.append({
            "method": method, "path": path, "description": description,
            "parameters": parameters or [], "response_example": response_example or {},
        })

    def generate(self) -> Dict[str, Any]:
        return {"title": self.title, "version": self.version,
                "endpoints": self.endpoints, "total_endpoints": len(self.endpoints)}

    def generate_markdown(self) -> str:
        lines = [f"# {self.title} v{self.version}", ""]
        for ep in self.endpoints:
            lines.append(f"## {ep['method'].upper()} {ep['path']}")
            lines.append(f"{ep['description']}")
            lines.append("")
        return "\n".join(lines)

    def list_endpoints(self) -> List[Dict[str, Any]]:
        return self.endpoints
