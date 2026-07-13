"""
Confidence Fusion
Layer 2: Research Engine — Module 8

Fuses confidence from multiple research modules:
- Multi-source confidence fusion
- Bayesian-style updating
- Evidence-weighted confidence
- Final confidence calculation
"""

from typing import Dict, List, Optional
from layers.layer02_research.shared.confidence_engine import ConfidenceEngine, ConfidenceResult


class ConfidenceFusion:
    """Fuse confidence from multiple module results."""

    def __init__(self, confidence_engine: Optional[ConfidenceEngine] = None):
        self._engine = confidence_engine or ConfidenceEngine()

    def fuse(
        self,
        module_confidences: Dict[str, float],
        evidence: Optional[List[str]] = None,
    ) -> ConfidenceResult:
        """Fuse multiple module confidence scores into one."""
        if not module_confidences:
            return ConfidenceResult(confidence=0.0, risk_level="CRITICAL")

        # Bayesian-style: multiply normalized confidences
        # Each module's confidence is treated as P(module_correct)
        combined = 1.0
        for module, conf in module_confidences.items():
            conf = max(0.01, min(0.99, conf))  # Avoid 0 or 1
            combined *= conf

        # Normalize: geometric mean approach
        n = len(module_confidences)
        fused_confidence = combined ** (1.0 / n) if n > 0 else 0.0

        # Evidence boost
        ev_count = len(evidence) if evidence else 0
        evidence_boost = min(0.1, ev_count * 0.02)

        final_confidence = min(1.0, fused_confidence + evidence_boost)

        # Risk level
        if final_confidence >= 0.85:
            risk_level = "VERY_LOW"
        elif final_confidence >= 0.70:
            risk_level = "LOW"
        elif final_confidence >= 0.50:
            risk_level = "MEDIUM"
        elif final_confidence >= 0.30:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Reasons
        reasons = []
        for module, conf in sorted(module_confidences.items(), key=lambda x: x[1]):
            if conf >= 0.8:
                reasons.append(f"{module} confidence is high ({conf:.0%})")
            elif conf < 0.4:
                reasons.append(f"{module} confidence is low ({conf:.0%})")

        ev = evidence or []
        return ConfidenceResult(
            confidence=round(final_confidence, 3),
            reasons=reasons,
            risk_level=risk_level,
            evidence=ev,
            metadata={"module_count": n, "raw_fused": round(fused_confidence, 3)},
        )

    def from_scores(
        self,
        scores: Dict[str, float],
        evidence: Optional[List[str]] = None,
    ) -> ConfidenceResult:
        """Convert 0-10 scores to confidence and fuse."""
        module_confidences = {k: v / 10.0 for k, v in scores.items()}
        return self.fuse(module_confidences, evidence)
