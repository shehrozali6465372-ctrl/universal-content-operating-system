"""PromptSimilarity — measure similarity between prompts."""
from __future__ import annotations

from typing import Any, Dict, List


class PromptSimilarity:
    """Measure similarity between prompts using multiple methods."""

    @staticmethod
    def cosine_similarity_tokens(a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        return len(intersection) / (len(words_a) * len(words_b)) ** 0.5

    @staticmethod
    def jaccard_similarity(a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a and not words_b:
            return 1.0
        union = words_a | words_b
        if not union:
            return 0.0
        return len(words_a & words_b) / len(union)

    @staticmethod
    def overlap_coefficient(a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / min(len(words_a), len(words_b))

    def find_most_similar(self, target: str, candidates: List[str]) -> Dict[str, Any]:
        if not candidates:
            return {"most_similar": "", "similarity": 0.0}
        scores = [(c, self.jaccard_similarity(target, c)) for c in candidates]
        scores.sort(key=lambda x: x[1], reverse=True)
        return {"most_similar": scores[0][0], "similarity": scores[0][1],
                "all_scores": {s[0]: round(s[1], 4) for s in scores}}

    def cluster(self, prompts: List[str], threshold: float = 0.3) -> List[List[str]]:
        if not prompts:
            return []
        clusters: List[List[str]] = [[prompts[0]]]
        for p in prompts[1:]:
            placed = False
            for cluster in clusters:
                if self.jaccard_similarity(p, cluster[0]) > threshold:
                    cluster.append(p)
                    placed = True
                    break
            if not placed:
                clusters.append([p])
        return clusters
