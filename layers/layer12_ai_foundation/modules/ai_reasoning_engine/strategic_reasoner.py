"""StrategicReasoner — long-term strategic reasoning and planning."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class StrategicReasoner:
    """Long-term strategic reasoning and multi-step planning."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def plan(self, goal: str, constraints: Optional[List[str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.STRATEGIC)
        chain.add_step(ReasoningStep(step_type="goal", content=goal))
        if constraints:
            for c in constraints:
                chain.add_step(ReasoningStep(step_type="constraint", content=c))
        phases = ["Assessment", "Design", "Implementation", "Evaluation"]
        for phase in phases:
            chain.add_step(ReasoningStep(step_type="phase", content=phase, confidence=0.7))
        chain.conclusion = f"Strategic plan with {len(phases)} phases for: {goal}"
        chain.confidence = 0.75
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def risk_assessment(self, action: str, risks: Optional[List[str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.STRATEGIC)
        chain.add_step(ReasoningStep(step_type="action", content=action))
        risks = risks or ["Market risk", "Technical risk", "Resource risk"]
        for r in risks:
            chain.add_step(ReasoningStep(step_type="risk", content=r, confidence=0.6))
        chain.conclusion = f"Assessed {len(risks)} risks for: {action}"
        chain.confidence = 0.7
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
