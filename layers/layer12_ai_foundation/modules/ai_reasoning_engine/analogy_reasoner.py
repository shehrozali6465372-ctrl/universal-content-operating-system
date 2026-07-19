"""AnalogyReasoner — draw insights through analogical reasoning."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class AnalogyReasoner:
    """Draw insights through analogical reasoning between domains."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def draw_analogy(self, source_domain: str, target_domain: str,
                     mappings: Optional[Dict[str, str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.CREATIVE)
        chain.add_step(ReasoningStep(step_type="source", content=f"Source domain: {source_domain}"))
        chain.add_step(ReasoningStep(step_type="target", content=f"Target domain: {target_domain}"))
        if mappings:
            for k, v in mappings.items():
                chain.add_step(ReasoningStep(step_type="mapping", content=f"{k} → {v}"))
        chain.conclusion = f"Analogy: {source_domain} is to {target_domain}"
        chain.confidence = 0.6
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
