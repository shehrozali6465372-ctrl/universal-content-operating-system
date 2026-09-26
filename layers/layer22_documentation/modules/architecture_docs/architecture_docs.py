"""Production-safe architecture documentation generation."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any, Dict, List, Optional


class ArchitectureDocs:
    """Build validated architecture documentation with isolated state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._layers: List[Dict[str, Any]] = []
        self._components: List[Dict[str, Any]] = []
        self._decisions: List[Dict[str, Any]] = []

    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-blank string")
        return value.strip()

    @staticmethod
    def _require_non_negative_int(value: int, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
        return value

    def add_layer(self, name: str, description: str, modules: int = 0) -> None:
        layer = {
            "name": self._require_text(name, "name"),
            "description": self._require_text(description, "description"),
            "modules": self._require_non_negative_int(modules, "modules"),
        }
        with self._lock:
            if any(item["name"] == layer["name"] for item in self._layers):
                raise ValueError(f"duplicate layer: {layer['name']}")
            self._layers.append(layer)

    def add_component(
        self,
        name: str,
        description: str,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        if dependencies is not None and (
            not isinstance(dependencies, list)
            or not all(isinstance(item, str) and item.strip() for item in dependencies)
        ):
            raise TypeError("dependencies must be a list of non-blank strings")
        component = {
            "name": self._require_text(name, "name"),
            "description": self._require_text(description, "description"),
            "dependencies": [item.strip() for item in dependencies or []],
        }
        with self._lock:
            if any(item["name"] == component["name"] for item in self._components):
                raise ValueError(f"duplicate component: {component['name']}")
            self._components.append(component)

    def add_decision(self, title: str, status: str, description: str = "") -> None:
        decision = {
            "title": self._require_text(title, "title"),
            "status": self._require_text(status, "status"),
            "description": (
                self._require_text(description, "description") if description.strip() else ""
            ),
        }
        with self._lock:
            if any(item["title"] == decision["title"] for item in self._decisions):
                raise ValueError(f"duplicate decision: {decision['title']}")
            self._decisions.append(decision)

    def generate(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "layers": deepcopy(self._layers),
                "components": deepcopy(self._components),
                "decisions": deepcopy(self._decisions),
                "summary": {
                    "total_layers": len(self._layers),
                    "total_components": len(self._components),
                    "total_decisions": len(self._decisions),
                },
            }

    def generate_markdown(self) -> str:
        with self._lock:
            layers = deepcopy(self._layers)
            components = deepcopy(self._components)
            decisions = deepcopy(self._decisions)
        lines = ["# Architecture Documentation", "", "## Layers"]
        for layer in layers:
            lines.append(
                f"- **{layer['name']}**: {layer['description']} "
                f"({layer['modules']} modules)"
            )
        lines.extend(["", "## Components"])
        for component in components:
            dependencies = component["dependencies"]
            suffix = f" — depends on: {', '.join(dependencies)}" if dependencies else ""
            lines.append(f"- **{component['name']}**: {component['description']}{suffix}")
        lines.extend(["", "## Decisions"])
        for decision in decisions:
            lines.append(
                f"- **{decision['title']}** [{decision['status']}]: "
                f"{decision['description']}"
            )
        return "\n".join(lines)
