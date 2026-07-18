"""ResponseSelector — select the best response from multiple candidates."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ModelResponse


class ResponseSelector:
    """Select the best response from multiple model candidates."""

    STRATEGIES = ("highest_confidence", "best_ranked", "ensemble", "quality_first")

    def __init__(self, strategy: str = "highest_confidence") -> None:
        self.strategy = strategy if strategy in self.STRATEGIES else "highest_confidence"
        self._history: List[Dict[str, Any]] = []

    def select(self, responses: List[ModelResponse],
               scores: Optional[Dict[str, float]] = None) -> Optional[ModelResponse]:
        if not responses:
            return None
        successful = [r for r in responses if r.is_success]
        if not successful:
            return None

        if self.strategy == "highest_confidence":
            best = max(successful, key=lambda r: r.confidence)
        elif self.strategy == "best_ranked" and scores:
            best = max(successful, key=lambda r: scores.get(r.model, 0.0))
        elif self.strategy == "quality_first":
            best = max(successful, key=lambda r: (r.confidence, -r.latency_ms))
        elif self.strategy == "ensemble":
            best = max(successful, key=lambda r: r.confidence * 0.7 + (1.0 - min(r.latency_ms / 5000, 1.0)) * 0.3)
        else:
            best = max(successful, key=lambda r: r.confidence)

        self._history.append({"selected": best.model, "strategy": self.strategy})
        return best

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
