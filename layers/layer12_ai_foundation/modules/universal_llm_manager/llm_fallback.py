"""LLMFallback — Fallback chain between providers."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

class LLMFallback:
    def __init__(self) -> None:
        self._chains: Dict[str, List[str]] = {}
        self._current_index: Dict[str, int] = {}
    def set_chain(self, name: str, providers: List[str]) -> None:
        self._chains[name] = list(providers)
        self._current_index[name] = 0
    def get_next(self, name: str) -> Optional[str]:
        chain = self._chains.get(name, [])
        if not chain:
            return None
        idx = self._current_index.get(name, 0)
        if idx < len(chain):
            return chain[idx]
        return None
    def report_failure(self, name: str) -> Optional[str]:
        idx = self._current_index.get(name, 0)
        self._current_index[name] = idx + 1
        return self.get_next(name)
    def report_success(self, name: str) -> None:
        self._current_index[name] = 0
    def get_stats(self) -> Dict[str, Any]:
        return {"chains": len(self._chains), "chains_detail": {k: len(v) for k, v in self._chains.items()}}
