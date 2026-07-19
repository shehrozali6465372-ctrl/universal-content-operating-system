"""AIFallback — fallback strategies when components fail."""
from __future__ import annotations
from typing import Any, Dict, List

class AIFallback:
    def __init__(self) -> None:
        self._log: List[Dict[str, Any]] = []
    def handle_failure(self, component: str, error: str) -> Dict[str, Any]:
        fallback = {"original": component, "fallback": "retry", "error": error}
        self._log.append(fallback); return fallback
    def get_log(self) -> List[Dict[str, Any]]: return list(self._log)
