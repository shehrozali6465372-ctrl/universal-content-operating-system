"""PromptRanker — rank prompts by effectiveness and quality."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class PromptRanker:
    """Rank multiple prompts by effectiveness and quality."""

    def __init__(self) -> None:
        self._ranking_history: List[Dict[str, Any]] = []

    def rank(self, prompts: List[Dict[str, Any]],
             criteria: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        criteria = criteria or {"quality": 0.3, "relevance": 0.25, "clarity": 0.25,
                                "conciseness": 0.2}
        ranked = []
        for p in prompts:
            score = sum(p.get(k, 0.5) * w for k, w in criteria.items())
            ranked.append({**p, "total_score": score})
        ranked.sort(key=lambda x: x["total_score"], reverse=True)
        for i, r in enumerate(ranked):
            r["rank"] = i + 1
        self._ranking_history.append(ranked)
        return ranked

    def get_top(self, prompts: List[Dict[str, Any]], top_n: int = 1) -> List[Dict[str, Any]]:
        return self.rank(prompts)[:top_n]

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._ranking_history)
