"""EnsembleAI — combine multiple model responses into superior output."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ModelResponse
from .consensus_engine import ConsensusEngine
from .voting_engine import VotingEngine
from .ranking_engine import RankingEngine
from .confidence_engine import ConfidenceEngine
from .response_selector import ResponseSelector


class EnsembleAI:
    """Combine multiple model responses into superior output using ensemble methods."""

    def __init__(self, consensus_method: str = "majority",
                 voting_strategy: str = "plurality") -> None:
        self.consensus = ConsensusEngine(consensus_method)
        self.voting = VotingEngine(voting_strategy)
        self.ranking = RankingEngine()
        self.confidence = ConfidenceEngine()
        self.selector = ResponseSelector("highest_confidence")
        self._history: List[Dict[str, Any]] = []

    def ensemble(self, responses: List[ModelResponse],
                 weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        if not responses:
            return {"best": None, "consensus": None, "ranking": [], "confidence": {}}

        successful = [r for r in responses if r.is_success]
        if not successful:
            return {"best": None, "consensus": None, "ranking": [], "confidence": {}}

        # Run all engines
        consensus = self.consensus.find_consensus(successful, weights)
        vote = self.voting.vote(successful)
        ranked = self.ranking.rank(successful)
        conf = self.confidence.calculate(successful)
        best = self.selector.select(successful)

        result = {
            "best": best,
            "consensus": consensus,
            "vote": vote,
            "ranking": ranked,
            "confidence": conf,
            "model_count": len(successful),
        }
        self._history.append({
            "consensus_score": consensus.agreement_score,
            "confidence": conf["overall_confidence"],
            "best_model": best.model if best else None,
        })
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
