"""Dependency Manager — Layer dependency graph."""
from __future__ import annotations
from typing import Dict, List, Optional


class LayerDependencies:
    """Manage dependencies between layers."""

    LAYER_ORDER = [
        "layer01_core", "layer02_research", "layer03_intelligence",
        "layer04_writing", "layer05_image", "layer06_quality",
        "layer07_publishing", "layer08_analytics", "layer09_learning",
        "layer10_master",
    ]

    DEFAULT_DEPS: Dict[str, List[str]] = {
        "layer02_research": ["layer01_core"],
        "layer03_intelligence": ["layer01_core", "layer02_research"],
        "layer04_writing": ["layer01_core", "layer03_intelligence"],
        "layer05_image": ["layer01_core", "layer03_intelligence"],
        "layer06_quality": ["layer01_core", "layer04_writing", "layer05_image"],
        "layer07_publishing": ["layer01_core", "layer06_quality"],
        "layer08_analytics": ["layer01_core", "layer07_publishing"],
        "layer09_learning": ["layer01_core", "layer08_analytics"],
        "layer10_master": ["layer01_core", "layer02_research", "layer03_intelligence",
                           "layer04_writing", "layer05_image", "layer06_quality",
                           "layer07_publishing", "layer08_analytics", "layer09_learning"],
    }

    def __init__(self) -> None:
        self._deps: Dict[str, List[str]] = dict(self.DEFAULT_DEPS)
        self._custom_deps: Dict[str, List[str]] = {}

    def get_dependencies(self, layer: str) -> List[str]:
        return list(self._deps.get(layer, self._custom_deps.get(layer, [])))

    def add_dependency(self, layer: str, depends_on: str) -> None:
        if layer not in self._custom_deps:
            self._custom_deps[layer] = []
        if depends_on not in self._custom_deps[layer]:
            self._custom_deps[layer].append(depends_on)

    def resolve_order(self, layers: Optional[List[str]] = None) -> List[str]:
        layers = layers or list(self.LAYER_ORDER)
        resolved: List[str] = []
        remaining = set(layers)
        while remaining:
            ready = [
                l for l in remaining
                if all(d in resolved for d in self.get_dependencies(l))
            ]
            if not ready:
                ready = list(remaining)
            resolved.extend(ready)
            remaining -= set(ready)
        return resolved

    def validate(self) -> bool:
        order = self.resolve_order()
        return len(order) > 0

    def get_ready_layers(self, completed: List[str],
                          layers: Optional[List[str]] = None) -> List[str]:
        layers = layers or list(self.LAYER_ORDER)
        remaining = [l for l in layers if l not in completed]
        return [
            l for l in remaining
            if all(d in completed for d in self.get_dependencies(l))
        ]

    def is_satisfied(self, completed: List[str], layer: str) -> bool:
        deps = self.get_dependencies(layer)
        return all(d in completed for d in deps)
