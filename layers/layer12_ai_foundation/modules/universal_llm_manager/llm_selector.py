"""LLMSelector — Select best model for a task."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

class LLMSelector:
    def __init__(self) -> None:
        self._criteria: Dict[str, float] = {"quality": 0.4, "speed": 0.3, "cost": 0.3}

    def select(self, models: List[Dict[str, Any]], task_type: str = "general") -> Optional[Dict[str, Any]]:
        if not models:
            return None
        scored = []
        for m in models:
            score = (m.get("quality", 0.5) * self._criteria["quality"] +
                     m.get("speed", 0.5) * self._criteria["speed"] +
                     (1.0 - m.get("cost", 0.5)) * self._criteria["cost"])
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None

    def set_criteria(self, criteria: Dict[str, float]) -> None:
        self._criteria = criteria

    def get_stats(self) -> Dict[str, Any]:
        return {"criteria": dict(self._criteria)}
