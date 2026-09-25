"""CostFallback — fallback when budget exceeded."""
from __future__ import annotations

from typing import Any, Dict, List


class CostFallback:
    def __init__(self) -> None:
        self._fallback_log: List[Dict[str, Any]] = []

    def get_fallback_model(self, current_model: str, budget_remaining: float) -> str:
        if budget_remaining < 0.001:
            return "gpt-5.6-luna"
        if budget_remaining < 0.01:
            return "gemini-3.8-flash"
        return current_model

    def log(self, original: str, fallback: str, reason: str) -> None:
        self._fallback_log.append(
            {"from": original, "to": fallback, "reason": reason}
        )

    def get_log(self) -> List[dict]:
        return list(self._fallback_log)
