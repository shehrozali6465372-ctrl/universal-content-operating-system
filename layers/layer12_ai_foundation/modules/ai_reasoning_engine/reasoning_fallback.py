"""ReasoningFallback — fallback strategies when primary reasoning fails."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ReasoningResult


class ReasoningFallback:
    """Fallback strategies when primary reasoning approaches fail."""

    def __init__(self) -> None:
        self._fallback_log: List[Dict[str, Any]] = []

    def attempt_fallback(self, problem: str, failed_approaches: List[str]) -> ReasoningResult:
        available = ["logical", "analytical", "creative", "strategic"]
        remaining = [a for a in available if a not in failed_approaches]
        approach = remaining[0] if remaining else "simple"
        self._fallback_log.append({"problem": problem[:100],
                                    "approach": approach,
                                    "failed": failed_approaches})
        return ReasoningResult(
            answer=f"Fallback reasoning ({approach}) for: {problem[:50]}",
            confidence=0.4,
        )

    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._fallback_log)
