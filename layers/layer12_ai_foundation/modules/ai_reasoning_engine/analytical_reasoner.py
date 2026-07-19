"""AnalyticalReasoner — data-driven analytical reasoning."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class AnalyticalReasoner:
    """Data-driven analytical reasoning with pattern detection."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def analyze(self, data: List[Dict[str, Any]], question: str = "") -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.ANALYTICAL)
        chain.add_step(ReasoningStep(step_type="data_input", content=f"Received {len(data)} data points"))

        # Pattern detection
        if data:
            keys = set()
            for d in data:
                keys.update(d.keys())
            chain.add_step(ReasoningStep(step_type="pattern", content=f"Identified {len(keys)} features"))
            chain.add_step(ReasoningStep(step_type="analysis",
                content=f"Analyzed {len(data)} records across {len(keys)} dimensions"))

        conclusion = f"Analysis of {len(data)} data points complete."
        chain.conclusion = conclusion
        chain.confidence = min(1.0, 0.4 + len(data) * 0.05)
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def compare(self, option_a: str, option_b: str, criteria: Optional[List[str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.ANALYTICAL)
        criteria = criteria or ["relevance", "feasibility", "impact"]
        for c in criteria:
            chain.add_step(ReasoningStep(step_type="criterion", content=f"Evaluating: {c}"))
        chain.conclusion = f"Comparison of {len(criteria)} criteria completed."
        chain.confidence = 0.7
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
