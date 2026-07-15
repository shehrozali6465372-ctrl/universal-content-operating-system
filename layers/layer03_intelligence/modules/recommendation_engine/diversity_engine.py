"""Diversity Engine - Ensures recommendations are diverse across topics and types."""
from __future__ import annotations
from typing import Any, Dict, List


class DiversityResult:
    __slots__ = ("selected", "diversity_score", "coverage", "clusters")
    def __init__(self) -> None:
        self.selected: List[Any] = []
        self.diversity_score = 0.0
        self.coverage = 0.0
        self.clusters: Dict[str, int] = {}
    def to_dict(self) -> Dict:
        return {"selected_count": len(self.selected), "diversity_score": round(self.diversity_score, 3),
                "coverage": round(self.coverage, 3), "clusters": dict(self.clusters)}


class DiversityEngine:
    def __init__(self, max_per_cluster: int = 2) -> None:
        self._max_per = max_per_cluster

    def diversify(self, ranked: List[Any], category_fn=None) -> DiversityResult:
        result = DiversityResult()
        if not ranked:
            return result

        clusters: Dict[str, int] = {}
        selected = []
        for c in ranked:
            cluster = category_fn(c.topic) if category_fn else c.source
            count = clusters.get(cluster, 0)
            if count < self._max_per:
                selected.append(c)
                clusters[cluster] = count + 1

        result.selected = selected
        result.clusters = clusters
        result.diversity_score = len(clusters) / max(len(ranked), 1)
        result.coverage = len(selected) / max(len(ranked), 1)
        return result
