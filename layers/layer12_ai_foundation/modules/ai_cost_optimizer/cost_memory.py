"""CostMemory — remember spending patterns."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class CostMemory:
    def __init__(self, max_entries: int = 1000) -> None:
        self.max_entries = max_entries
        self._history: List[Dict[str, Any]] = []
    def store(self, provider: str, model: str, cost: float, metadata: Dict[str, Any] | None = None) -> None:
        self._history.append({"provider": provider, "model": model, "cost": cost,
                              "metadata": metadata or {}, "timestamp": time.time()})
        if len(self._history) > self.max_entries:
            self._history = self._history[-self.max_entries:]
    def get_avg_cost(self, provider: str = "") -> float:
        entries = [e for e in self._history if not provider or e["provider"] == provider]
        return sum(e["cost"] for e in entries) / max(len(entries), 1)
    def get_spending_by_provider(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._history:
            totals[e["provider"]] = totals.get(e["provider"], 0.0) + e["cost"]
        return totals
    def get_spending_by_model(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._history:
            totals[e["model"]] = totals.get(e["model"], 0.0) + e["cost"]
        return totals
    def count(self) -> int:
        return len(self._history)
    def clear(self) -> None:
        self._history.clear()
