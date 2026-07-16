"""Confidence Fusion — Reliability-based confidence fusion across layers."""
from __future__ import annotations
from typing import List

from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore


class ConfidenceFusion:
    """Fuse confidence scores using reliability-weighted averaging."""

    def __init__(self) -> None:
        self._fuse_count = 0

    def fuse(self, module_scores: List[ModuleScore]) -> float:
        """Fuse confidences with reliability weighting."""
        if not module_scores:
            return 0.0

        # Each module's confidence contributes based on its own reliability
        # Higher confidence modules have more influence
        weighted_sum = 0.0
        weight_total = 0.0

        for ms in module_scores:
            # Reliability = confidence squared (rewards high-confidence modules more)
            reliability = ms.confidence ** 2
            weighted_sum += ms.confidence * reliability
            weight_total += reliability

        if weight_total == 0:
            return 0.0

        base_confidence = weighted_sum / weight_total

        # Apply penalty if there are critical issues
        critical_count = sum(len(ms.critical_issues) for ms in module_scores)
        critical_penalty = min(0.3, critical_count * 0.1)

        # Apply penalty for missing modules (reduces confidence)
        reported_names = {ms.module_name for ms in module_scores}
        all_names = {"content_quality", "fact_validation", "safety", "originality",
                     "seo", "platform_compliance", "brand_voice", "human_review"}
        missing = all_names - reported_names
        missing_penalty = len(missing) * 0.02

        final = max(0.0, base_confidence - critical_penalty - missing_penalty)
        self._fuse_count += 1
        return round(final, 3)

    def fuse_with_context(
        self,
        module_scores: List[ModuleScore],
        layer2_confidence: float = 0.5,
        layer3_confidence: float = 0.5,
    ) -> float:
        """Fuse with cross-layer context."""
        module_conf = self.fuse(module_scores)

        # Cross-layer weighting: Layer 2 (research) and Layer 3 (intelligence) provide context
        context_bonus = (layer2_confidence * 0.15 + layer3_confidence * 0.15)

        final = min(1.0, module_conf + context_bonus)
        self._fuse_count += 1
        return round(final, 3)

    @property
    def fuse_count(self) -> int:
        return self._fuse_count
