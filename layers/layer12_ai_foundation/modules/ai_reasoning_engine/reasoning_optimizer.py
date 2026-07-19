"""ReasoningOptimizer — optimize reasoning chains for efficiency."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ReasoningChain


class ReasoningOptimizer:
    """Optimize reasoning chains for efficiency and quality."""

    def __init__(self) -> None:
        self._optimizations: List[Dict[str, Any]] = []

    def optimize(self, chain: ReasoningChain) -> ReasoningChain:
        # Remove low-confidence steps that don't add value
        filtered_steps = []
        for step in chain.steps:
            if step.confidence >= 0.2 or step.step_type in ("conclusion", "premise"):
                filtered_steps.append(step)
        chain.steps = filtered_steps
        self._optimizations.append({"chain_id": chain.chain_id,
                                     "steps_removed": len(chain.steps) - len(filtered_steps)})
        return chain

    def prune_duplicates(self, chain: ReasoningChain) -> ReasoningChain:
        seen_contents = set()
        unique_steps = []
        for step in chain.steps:
            normalized = step.content.lower().strip()
            if normalized not in seen_contents:
                seen_contents.add(normalized)
                unique_steps.append(step)
        chain.steps = unique_steps
        return chain

    def get_optimizations(self) -> List[Dict[str, Any]]:
        return list(self._optimizations)
