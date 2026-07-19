"""CreativeReasoner — generate creative ideas and novel solutions."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class CreativeReasoner:
    """Generate creative ideas and novel solutions through brainstorming."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def brainstorm(self, topic: str, count: int = 5) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.CREATIVE)
        chain.add_step(ReasoningStep(step_type="topic", content=f"Brainstorming: {topic}"))
        ideas = [f"Idea {i+1} for {topic}" for i in range(count)]
        for idea in ideas:
            chain.add_step(ReasoningStep(step_type="idea", content=idea, confidence=0.6))
        chain.conclusion = f"Generated {count} creative ideas for '{topic}'"
        chain.confidence = 0.65
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, alternatives=ideas,
                                 reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def lateral_thinking(self, problem: str) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.CREATIVE)
        chain.add_step(ReasoningStep(step_type="problem", content=problem))
        approaches = ["Unconventional angle", "Reverse thinking", "Cross-domain transfer"]
        for a in approaches:
            chain.add_step(ReasoningStep(step_type="approach", content=a))
        chain.conclusion = f"Applied lateral thinking to: {problem}"
        chain.confidence = 0.55
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
