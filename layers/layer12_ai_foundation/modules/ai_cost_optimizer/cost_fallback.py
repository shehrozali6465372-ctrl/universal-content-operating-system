"""CostFallback — fallback when budget exceeded."""
from __future__ import annotations
from typing import Any, Dict, List

class CostFallback:
    def __init__(self) -> None:
        self._fallback_log: List[Dict[str, Any]] = []
    def get_fallback_model(self, current_model: str, budget_remaining: float) -> str:
        if budget_remaining < 0.001: return "gemini-2.0-flash"
        if budget_remaining < 0.01: return "gpt-4o-mini"
        return current_model
    def log(self, original: str, fallback: str, reason: str) -> None:
        self._fallback_log.append({"from": original, "to": fallback, "reason": reason})
    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._fallback_log)
