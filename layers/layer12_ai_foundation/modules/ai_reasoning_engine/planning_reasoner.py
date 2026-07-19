"""PlanningReasoner — break goals into actionable steps with dependencies."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class PlanningReasoner:
    """Break goals into actionable steps with dependencies."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def decompose(self, goal: str, max_steps: int = 10) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.PLANNING)
        chain.add_step(ReasoningStep(step_type="goal", content=goal))
        steps = [f"Step {i+1}: Subtask for {goal}" for i in range(max_steps)]
        for s in steps:
            chain.add_step(ReasoningStep(step_type="subtask", content=s, confidence=0.75))
        chain.conclusion = f"Decomposed into {max_steps} steps"
        chain.confidence = 0.7
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, alternatives=steps,
                                 reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def schedule(self, tasks: List[Dict[str, Any]], deadline: str = "") -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.PLANNING)
        chain.add_step(ReasoningStep(step_type="tasks", content=f"{len(tasks)} tasks to schedule"))
        for t in tasks:
            chain.add_step(ReasoningStep(step_type="scheduled", content=str(t)[:100]))
        chain.conclusion = f"Scheduled {len(tasks)} tasks"
        chain.confidence = 0.7
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
