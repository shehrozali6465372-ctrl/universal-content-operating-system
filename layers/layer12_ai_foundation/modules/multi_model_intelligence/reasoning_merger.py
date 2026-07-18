"""ReasoningMerger — merge reasoning chains from multiple models."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ModelResponse


class ReasoningMerger:
    """Merge reasoning chains from multiple models into a unified answer."""

    def __init__(self, strategy: str = "weighted_merge") -> None:
        self.strategy = strategy
        self._history: List[Dict[str, Any]] = []

    def merge(self, responses: List[ModelResponse],
              weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        if not responses:
            return {"merged": "", "confidence": 0.0, "sources": 0}

        successful = [r for r in responses if r.is_success]
        if not successful:
            return {"merged": "", "confidence": 0.0, "sources": 0}

        if self.strategy == "weighted_merge":
            result = self._weighted_merge(successful, weights or {})
        elif self.strategy == "concatenate":
            result = self._concatenate_merge(successful)
        elif self.strategy == "best_pick":
            result = self._best_pick_merge(successful)
        else:
            result = self._weighted_merge(successful, weights or {})

        self._history.append(result)
        return result

    def _weighted_merge(self, responses: List[ModelResponse],
                        weights: Dict[str, float]) -> Dict[str, Any]:
        total_weight = 0.0
        weighted_confidence = 0.0
        best_content = ""
        best_score = -1.0

        for r in responses:
            w = weights.get(r.model, 1.0)
            score = r.confidence * w
            weighted_confidence += score
            total_weight += w
            if score > best_score:
                best_score = score
                best_content = r.content

        avg_confidence = weighted_confidence / total_weight if total_weight else 0.0
        return {"merged": best_content, "confidence": avg_confidence,
                "sources": len(responses),
                "method": "weighted_merge"}

    def _concatenate_merge(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        parts = []
        total_conf = 0.0
        for r in responses:
            parts.append(f"[{r.model}]: {r.content}")
            total_conf += r.confidence
        return {"merged": "\n\n".join(parts),
                "confidence": total_conf / len(responses),
                "sources": len(responses), "method": "concatenate"}

    def _best_pick_merge(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        best = max(responses, key=lambda r: r.confidence)
        return {"merged": best.content, "confidence": best.confidence,
                "sources": len(responses), "method": "best_pick"}

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
