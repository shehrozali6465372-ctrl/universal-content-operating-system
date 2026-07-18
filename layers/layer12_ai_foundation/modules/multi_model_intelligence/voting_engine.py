"""VotingEngine — democratic model selection via weighted voting."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ModelResponse, VoteResult


class VotingEngine:
    """Democratic model selection via weighted voting."""

    STRATEGIES = ("plurality", "ranked_choice", "borda_count", "weighted")

    def __init__(self, strategy: str = "plurality", weights: Optional[Dict[str, float]] = None) -> None:
        self.strategy = strategy if strategy in self.STRATEGIES else "plurality"
        self.weights = weights or {}
        self._history: List[Dict[str, Any]] = []

    def vote(self, responses: List[ModelResponse]) -> Optional[VoteResult]:
        if not responses:
            return None
        successful = [r for r in responses if r.is_success]
        if not successful:
            return None

        if self.strategy == "plurality":
            return self._plurality_vote(successful)
        elif self.strategy == "ranked_choice":
            return self._ranked_choice_vote(successful)
        elif self.strategy == "borda_count":
            return self._borda_count_vote(successful)
        elif self.strategy == "weighted":
            return self._weighted_vote(successful)
        return self._plurality_vote(successful)

    def _plurality_vote(self, responses: List[ModelResponse]) -> VoteResult:
        # Each model votes for the response with highest score
        candidates: Dict[str, int] = {}
        voters: Dict[str, List[str]] = {}
        for r in responses:
            # Simple: the content with highest confidence gets a vote from each responder
            pass

        # Actually, in plurality, each model's response IS the candidate
        # and we rank them by confidence to pick the winner
        sorted_r = sorted(responses, key=lambda r: r.confidence, reverse=True)
        winner = sorted_r[0]
        return VoteResult(candidate=winner.content, votes=len(responses),
                          voters=[r.model for r in responses],
                          weight=winner.confidence)

    def _ranked_choice_vote(self, responses: List[ModelResponse]) -> VoteResult:
        if len(responses) <= 1:
            r = responses[0]
            return VoteResult(candidate=r.content, votes=1, voters=[r.model])
        # First round: highest confidence wins
        sorted_r = sorted(responses, key=lambda r: r.confidence, reverse=True)
        return VoteResult(candidate=sorted_r[0].content,
                          votes=len(responses),
                          voters=[r.model for r in sorted_r])

    def _borda_count_vote(self, responses: List[ModelResponse]) -> VoteResult:
        scores: Dict[str, float] = {}
        voter_map: Dict[str, List[str]] = {}
        n = len(responses)
        for rank_idx, r in enumerate(sorted(responses, key=lambda x: x.confidence, reverse=True)):
            borda = n - rank_idx - 1
            scores[r.content] = scores.get(r.content, 0) + borda
            voter_map.setdefault(r.content, []).append(r.model)

        winner = max(scores, key=lambda k: scores[k])
        return VoteResult(candidate=winner, votes=int(scores[winner]),
                          voters=voter_map.get(winner, []),
                          weight=1.0)

    def _weighted_vote(self, responses: List[ModelResponse]) -> VoteResult:
        best_score = -1.0
        best_r = responses[0]
        for r in responses:
            w = self.weights.get(r.model, 1.0)
            score = r.confidence * w
            if score > best_score:
                best_score = score
                best_r = r

        result = VoteResult(candidate=best_r.content, votes=len(responses),
                            voters=[r.model for r in responses],
                            weight=best_score)
        self._history.append(result.to_dict())
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
