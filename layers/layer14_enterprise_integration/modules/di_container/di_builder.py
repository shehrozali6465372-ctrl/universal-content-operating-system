"""DIBuilder — build dependency graph and auto-wire layers."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .di_container import DIContainer

class DIBuilder:
    def __init__(self) -> None:
        self.container = DIContainer()
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register_layer(self, layer_name: str, components: Dict[str, Any],
                       dependencies: Optional[List[str]] = None) -> None:
        self._registry[layer_name] = {
            'components': components, 'deps': dependencies or []
        }
        for name, instance in components.items():
            self.container.register(f'{layer_name}.{name}', instance)

    def resolve_chain(self) -> List[str]:
        """Topological sort of layers by dependencies."""
        visited: set = set()
        resolved: List[str] = []
        def dfs(layer: str) -> None:
            if layer in visited: return
            visited.add(layer)
            for dep in self._registry.get(layer, {}).get('deps', []):
                if dep in self._registry:
                    dfs(dep)
            resolved.append(layer)
        for layer in self._registry:
            dfs(layer)
        return resolved

    def verify_all(self) -> Dict[str, Any]:
        missing: List[str] = []
        resolved_order = self.resolve_chain()
        for layer in resolved_order:
            info = self._registry.get(layer, {})
            for dep in info.get('deps', []):
                if dep not in resolved_order:
                    missing.append(f'{layer} depends on {dep} but not registered')
        return {'valid': len(missing) == 0, 'missing': missing,
                'resolution_order': resolved_order,
                'layers_count': len(self._registry)}
