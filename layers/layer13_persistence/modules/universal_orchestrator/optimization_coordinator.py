"""optimization_coordinator.py — Optimization coordination."""
from __future__ import annotations
from typing import Any, Dict, List


class OptimizationCoordinator:
    """Coordinates optimizations across all stores."""

    def __init__(self) -> None:
        self._optimizations: List[Dict[str, Any]] = []
        self._applied: List[Dict[str, Any]] = []

    def suggest(self, store_name: str, suggestion: str,
                impact: str = "medium") -> None:
        self._optimizations.append({"store": store_name, "suggestion": suggestion,
                                     "impact": impact})

    def apply(self, index: int) -> bool:
        if 0 <= index < len(self._optimizations):
            opt = self._optimizations.pop(index)
            self._applied.append(opt)
            return True
        return False

    def get_suggestions(self) -> List[Dict[str, Any]]:
        return list(self._optimizations)

    def get_applied(self) -> List[Dict[str, Any]]:
        return list(self._applied)

    def stats(self) -> Dict[str, Any]:
        return {"suggestions": len(self._optimizations), "applied": len(self._applied)}
