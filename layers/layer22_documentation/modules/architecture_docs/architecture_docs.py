"""ArchitectureDocs — generate architecture documentation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ArchitectureDocs:
    def __init__(self) -> None:
        self._layers: List[Dict[str, Any]] = []
        self._components: List[Dict[str, Any]] = []
        self._decisions: List[Dict[str, Any]] = []

    def add_layer(self, name: str, description: str, modules: int = 0) -> None:
        self._layers.append({"name": name, "description": description, "modules": modules})

    def add_component(self, name: str, description: str, dependencies: Optional[List[str]] = None) -> None:
        self._components.append({"name": name, "description": description,
                                 "dependencies": dependencies or []})

    def add_decision(self, title: str, status: str, description: str = "") -> None:
        self._decisions.append({"title": title, "status": status, "description": description})

    def generate(self) -> Dict[str, Any]:
        return {"layers": self._layers, "components": self._components,
                "decisions": self._decisions,
                "summary": {"total_layers": len(self._layers),
                           "total_components": len(self._components),
                           "total_decisions": len(self._decisions)}}

    def generate_markdown(self) -> str:
        lines = ["# Architecture Documentation", ""]
        lines.append("## Layers")
        for layer in self._layers:
            lines.append(f"- **{layer['name']}**: {layer['description']} ({layer['modules']} modules)")
        lines.append("")
        lines.append("## Components")
        for comp in self._components:
            lines.append(f"- **{comp['name']}**: {comp['description']}")
        return "\n".join(lines)
