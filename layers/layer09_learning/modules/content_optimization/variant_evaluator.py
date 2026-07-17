"""Variant Evaluator — Compare original vs optimized content variants."""
from __future__ import annotations
from typing import Any, Dict, List


class VariantComparison:
    """Comparison between original and variant content."""

    __slots__ = ("variant_id", "original_score", "variant_score",
                 "improvement", "improvement_pct", "winner",
                 "dimension_scores")

    def __init__(self, variant_id: str = "") -> None:
        self.variant_id = variant_id
        self.original_score: float = 0.0
        self.variant_score: float = 0.0
        self.improvement: float = 0.0
        self.improvement_pct: float = 0.0
        self.winner: str = "original"
        self.dimension_scores: Dict[str, Dict[str, float]] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "original_score": round(self.original_score, 3),
            "variant_score": round(self.variant_score, 3),
            "improvement_pct": round(self.improvement_pct, 2),
            "winner": self.winner,
        }


class VariantEvaluator:
    """Evaluate and compare content variants against the original."""

    def __init__(self) -> None:
        self._comparisons: List[VariantComparison] = []

    def evaluate(self, original: str, variant_content: str,
                 variant_id: str = "") -> VariantComparison:
        comp = VariantComparison(variant_id)
        orig_score = self._score_content(original)
        var_score = self._score_content(variant_content)
        comp.original_score = orig_score
        comp.variant_score = var_score
        comp.improvement = round(var_score - orig_score, 3)
        if orig_score > 0:
            comp.improvement_pct = round((comp.improvement / orig_score) * 100, 2)
        comp.winner = "variant" if var_score > orig_score else "original"
        if abs(var_score - orig_score) < 0.01:
            comp.winner = "tie"
        self._comparisons.append(comp)
        return comp

    def evaluate_batch(self, original: str,
                       variants: List[Dict[str, Any]]) -> List[VariantComparison]:
        results = []
        for v in variants:
            comp = self.evaluate(original, v.get("content", ""), v.get("variant_id", ""))
            results.append(comp)
        return results

    def _score_content(self, content: str) -> float:
        if not content:
            return 0.0
        score = 0.3
        words = content.split()
        if words:
            unique = len(set(w.lower() for w in words)) / len(words)
            score += unique * 0.2
        sentences = content.count(".") + content.count("!") + content.count("?")
        if sentences > 0:
            avg_words = len(words) / max(1, sentences)
            if 8 <= avg_words <= 20:
                score += 0.2
        hooks = ["?", "!", "did you know", "imagine", "what if"]
        lower = content.lower()
        score += min(0.15, sum(0.05 for h in hooks if h in lower))
        if len(content) > 200:
            score += 0.15
        return round(min(1.0, score), 3)

    def get_best_variant(self) -> VariantComparison | None:
        if not self._comparisons:
            return None
        return max(self._comparisons, key=lambda c: c.variant_score)

    def get_comparisons(self) -> List[VariantComparison]:
        return list(self._comparisons)

    @property
    def evaluation_count(self) -> int:
        return len(self._comparisons)
