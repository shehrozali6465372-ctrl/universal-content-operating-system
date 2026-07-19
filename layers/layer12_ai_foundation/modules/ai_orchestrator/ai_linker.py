"""AILinker — link orchestrator to external AI foundation modules."""
from __future__ import annotations
from typing import Any, Dict

class AILinker:
    def __init__(self) -> None:
        self._links: Dict[str, Any] = {}
    def link(self, name: str, module: Any) -> None:
        self._links[name] = module
    def get(self, name: str) -> Any:
        return self._links.get(name)
    def list_links(self) -> Dict[str, str]:
        return {n: type(m).__name__ for n, m in self._links.items()}
    def count(self) -> int: return len(self._links)
