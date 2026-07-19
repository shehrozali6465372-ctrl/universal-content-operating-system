"""ChainBuilder — construct reasoning chains programmatically."""
from __future__ import annotations


from .models import ReasoningChain, ReasoningStep, ReasoningType


class ChainBuilder:
    """Build reasoning chains programmatically."""

    def __init__(self, reasoning_type: ReasoningType = ReasoningType.LOGICAL) -> None:
        self._chain = ReasoningChain(reasoning_type=reasoning_type)

    def add_premise(self, content: str, confidence: float = 0.9) -> "ChainBuilder":
        self._chain.add_step(ReasoningStep(step_type="premise", content=content, confidence=confidence))
        return self

    def add_observation(self, content: str, confidence: float = 0.7) -> "ChainBuilder":
        self._chain.add_step(ReasoningStep(step_type="observation", content=content, confidence=confidence))
        return self

    def add_inference(self, content: str, confidence: float = 0.8) -> "ChainBuilder":
        self._chain.add_step(ReasoningStep(step_type="inference", content=content, confidence=confidence))
        return self

    def add_evidence(self, content: str, confidence: float = 0.85) -> "ChainBuilder":
        self._chain.add_step(ReasoningStep(step_type="evidence", content=content, confidence=confidence))
        return self

    def set_conclusion(self, conclusion: str, confidence: float = 0.75) -> "ChainBuilder":
        self._chain.conclusion = conclusion
        self._chain.confidence = confidence
        self._chain.add_step(ReasoningStep(step_type="conclusion", content=conclusion, confidence=confidence))
        return self

    def build(self) -> ReasoningChain:
        return self._chain

    def reset(self, reasoning_type: ReasoningType = ReasoningType.LOGICAL) -> None:
        self._chain = ReasoningChain(reasoning_type=reasoning_type)
