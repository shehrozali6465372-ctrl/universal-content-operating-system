"""RankingEngine — score and rank multiple model responses."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ModelResponse, RankEntry


class RankingEngine:
    """Score and rank multiple model responses."""

    DEFAULT_WEIGHTS = {
        "quality": 0.3, "relevance": 0.25, "creativity": 0.2,
        "accuracy": 0.15, "conciseness": 0.1,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)
        self._history: List[Dict[str, Any]] = []

    def rank(self, responses: List[ModelResponse],
             criteria: Optional[Dict[str, float]] = None) -> List[RankEntry]:
        if not responses:
            return []

        weights = criteria or self.weights
        entries: List[RankEntry] = []

        for r in responses:
            breakdown: Dict[str, float] = {}
            total = 0.0
            for criterion, weight in weights.items():
                score = self._score_criterion(r, criterion)
                breakdown[criterion] = score
                total += score * weight

            entries.append(RankEntry(rank=0, response=r, score=total, breakdown=breakdown))

        entries.sort(key=lambda e: e.score, reverse=True)
        for i, entry in enumerate(entries, 1):
            entry.rank = i

        self._history.append([e.to_dict() for e in entries])
        return entries

    def get_top(self, responses: List[ModelResponse], top_n: int = 1,
                criteria: Optional[Dict[str, float]] = None) -> List[RankEntry]:
        return self.rank(responses, criteria)[:top_n]

    @staticmethod
    def _score_criterion(response: ModelResponse, criterion: str) -> float:
        content = response.content or ""
        if criterion == "quality":
            return min(1.0, response.confidence + (0.1 if len(content) > 50 else 0.0))
        elif criterion == "relevance":
            return response.confidence
        elif criterion == "creativity":
            unique_words = len(set(content.split())) / max(len(content.split()), 1)
            return min(1.0, unique_words * 2 + response.confidence * 0.5)
        elif criterion == "accuracy":
            return response.confidence
        elif criterion == "conciseness":
            length = len(content)
            if length < 50:
                return 1.0
            elif length < 200:
                return 0.8
            elif length < 500:
                return 0.6
            return 0.4
        return 0.5

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
