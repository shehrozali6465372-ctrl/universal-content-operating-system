"""Score Aggregator — Collect and weight scores from all quality modules."""
from __future__ import annotations
from typing import Dict, List, Optional

from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore


DEFAULT_WEIGHTS: Dict[str, float] = {
    "content_quality": 0.20,
    "fact_validation": 0.20,
    "safety": 0.20,
    "originality": 0.10,
    "seo": 0.10,
    "platform_compliance": 0.10,
    "brand_voice": 0.05,
    "human_review": 0.05,
}


class ScoreAggregator:
    """Aggregate scores from quality modules with configurable weights."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or dict(DEFAULT_WEIGHTS)
        self._normalize_weights()

    def aggregate(self, module_scores: List[ModuleScore]) -> float:
        """Compute weighted average score from module scores."""
        if not module_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for ms in module_scores:
            weight = self._weights.get(ms.module_name, 0.05)
            # Adjust weight by confidence — low confidence reduces impact
            effective_weight = weight * ms.confidence
            weighted_sum += ms.score * effective_weight
            total_weight += effective_weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 1)

    def aggregate_confidence(self, module_scores: List[ModuleScore]) -> float:
        """Compute overall confidence from module confidences."""
        if not module_scores:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0
        for ms in module_scores:
            weight = self._weights.get(ms.module_name, 0.05)
            weighted_sum += ms.confidence * weight
            total_weight += weight

        return round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.0

    def get_missing_modules(self, module_scores: List[ModuleScore]) -> List[str]:
        """Return modules that haven't reported scores."""
        reported = {ms.module_name for ms in module_scores}
        return [name for name in self._weights if name not in reported]

    def set_weight(self, module_name: str, weight: float) -> None:
        self._weights[module_name] = max(0.0, min(1.0, weight))
        self._normalize_weights()

    def get_weights(self) -> Dict[str, float]:
        return dict(self._weights)

    def _normalize_weights(self) -> None:
        total = sum(self._weights.values())
        if total > 0:
            self._weights = {k: v / total for k, v in self._weights.items()}
