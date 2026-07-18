"""ConsensusEngine — find agreement across multiple model responses."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .models import ConsensusResult, ModelResponse


class ConsensusEngine:
    """Find consensus across multiple model responses."""

    METHODS = ("majority", "weighted", "best_match", "semantic_similarity")

    def __init__(self, method: str = "majority") -> None:
        self.method = method if method in self.METHODS else "majority"
        self._history: List[Dict[str, Any]] = []

    def find_consensus(self, responses: List[ModelResponse],
                       weights: Optional[Dict[str, float]] = None) -> ConsensusResult:
        if not responses:
            return ConsensusResult(agreed_content="", agreement_score=0.0,
                                   participating_models=0, method=self.method)

        successful = [r for r in responses if r.is_success]
        if not successful:
            return ConsensusResult(agreed_content="", agreement_score=0.0,
                                   participating_models=0, method=self.method)

        if self.method == "majority":
            return self._majority_consensus(successful)
        elif self.method == "weighted":
            return self._weighted_consensus(successful, weights or {})
        elif self.method == "best_match":
            return self._best_match_consensus(successful)
        else:
            return self._majority_consensus(successful)

    def _majority_consensus(self, responses: List[ModelResponse]) -> ConsensusResult:
        # Normalize content for comparison
        normalized = {}
        for r in responses:
            key = self._normalize(r.content)
            if key not in normalized:
                normalized[key] = []
            normalized[key].append(r)

        if not normalized:
            return ConsensusResult(agreed_content="", agreement_score=0.0,
                                   participating_models=len(responses), method="majority")

        # Find largest group
        best_key = max(normalized, key=lambda k: len(normalized[k]))
        group = normalized[best_key]
        agreement = len(group) / len(responses) if responses else 0.0

        # Use highest confidence response as the agreed content
        best = max(group, key=lambda r: r.confidence)
        result = ConsensusResult(
            agreed_content=best.content,
            agreement_score=agreement,
            participating_models=len(responses),
            method="majority",
            details={"group_size": len(group), "unique_groups": len(normalized)},
        )
        self._history.append(result.to_dict())
        return result

    def _weighted_consensus(self, responses: List[ModelResponse],
                            weights: Dict[str, float]) -> ConsensusResult:
        # Score each response by weighted model confidence
        scored = []
        for r in responses:
            w = weights.get(r.model, 1.0)
            scored.append((r, r.confidence * w))

        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]
        total_score = sum(s for _, s in scored)
        agreement = scored[0][1] / total_score if total_score else 0.0

        result = ConsensusResult(
            agreed_content=best.content,
            agreement_score=agreement,
            participating_models=len(responses),
            method="weighted",
            details={"scores": {r.model: s for r, s in scored}},
        )
        self._history.append(result.to_dict())
        return result

    def _best_match_consensus(self, responses: List[ModelResponse]) -> ConsensusResult:
        # Find pairs of similar responses and pick the best from the largest cluster
        if len(responses) == 1:
            return ConsensusResult(
                agreed_content=responses[0].content,
                agreement_score=1.0,
                participating_models=1,
                method="best_match",
            )

        # Group by pairwise similarity
        clusters: List[List[ModelResponse]] = [[responses[0]]]
        for r in responses[1:]:
            placed = False
            for cluster in clusters:
                if self._similarity(r.content, cluster[0].content) > 0.5:
                    cluster.append(r)
                    placed = True
                    break
            if not placed:
                clusters.append([r])

        best_cluster = max(clusters, key=len)
        best = max(best_cluster, key=lambda r: r.confidence)
        agreement = len(best_cluster) / len(responses)

        return ConsensusResult(
            agreed_content=best.content,
            agreement_score=agreement,
            participating_models=len(responses),
            method="best_match",
            details={"cluster_sizes": [len(c) for c in clusters]},
        )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
