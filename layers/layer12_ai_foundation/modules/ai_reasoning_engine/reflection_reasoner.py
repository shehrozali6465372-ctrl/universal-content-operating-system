"""ReflectionReasoner — self-reflect on past decisions and reasoning quality."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class ReflectionReasoner:
    """Self-reflect on past decisions and reasoning quality."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []
        self._decisions: List[Dict[str, Any]] = []

    def reflect_on_decision(self, decision: str, outcome: str,
                            context: str = "") -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.REFLECTION)
        chain.add_step(ReasoningStep(step_type="decision", content=decision))
        chain.add_step(ReasoningStep(step_type="outcome", content=outcome))
        if context:
            chain.add_step(ReasoningStep(step_type="context", content=context))
        chain.add_step(ReasoningStep(step_type="reflection",
            content="Evaluating whether the decision was optimal"))
        quality = 0.7 if "success" in outcome.lower() else 0.4
        chain.conclusion = f"Decision quality: {'good' if quality > 0.5 else 'needs improvement'}"
        chain.confidence = quality
        elapsed = (time.time() - start) * 1000
        self._decisions.append({"decision": decision, "outcome": outcome, "quality": quality})
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def reflect_on_reasoning(self, chain_data: ReasoningChain) -> ReasoningResult:
        start = time.time()
        meta_chain = ReasoningChain(reasoning_type=ReasoningType.REFLECTION)
        meta_chain.add_step(ReasoningStep(step_type="analysis",
            content=f"Analyzing reasoning chain with {chain_data.step_count} steps"))
        step_confidences = [s.confidence for s in chain_data.steps]
        avg_conf = sum(step_confidences) / max(len(step_confidences), 1)
        meta_chain.add_step(ReasoningStep(step_type="metric",
            content=f"Average step confidence: {avg_conf:.2f}"))
        meta_chain.conclusion = f"Reasoning quality: {'good' if avg_conf > 0.5 else 'low'}"
        meta_chain.confidence = avg_conf
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=meta_chain, answer=meta_chain.conclusion,
                               confidence=meta_chain.confidence, reasoning_time_ms=elapsed)

    def get_decisions(self) -> List[Dict[str, Any]]:
        return list(self._decisions)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
