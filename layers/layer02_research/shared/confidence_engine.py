"""
Global Confidence Engine
Layer 2: Shared Component

Standardized confidence scoring across all research modules:
- Evidence-based confidence calculation
- Risk level assessment
- Multi-factor scoring
- Confidence aggregation across modules
"""

from typing import Dict, List, Optional


class ConfidenceResult:
    """Standardized confidence output for any decision."""

    __slots__ = ("confidence", "reasons", "risk_level", "evidence", "metadata")

    RISK_LEVELS = ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def __init__(
        self,
        confidence: float = 0.5,
        reasons: Optional[List[str]] = None,
        risk_level: str = "MEDIUM",
        evidence: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ):
        self.confidence = max(0.0, min(1.0, confidence))
        self.reasons = reasons or []
        self.risk_level = risk_level if risk_level in self.RISK_LEVELS else "MEDIUM"
        self.evidence = evidence or []
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "confidence": self.confidence,
            "reasons": self.reasons,
            "risk_level": self.risk_level,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }

    def add_reason(self, reason: str):
        self.reasons.append(reason)

    def add_evidence(self, evidence: str):
        self.evidence.append(evidence)

    def is_trustworthy(self) -> bool:
        """Is this result trustworthy enough to act on?"""
        return self.confidence >= 0.7 and self.risk_level in ("VERY_LOW", "LOW", "MEDIUM")

    def __str__(self) -> str:
        return f"ConfidenceResult(confidence={self.confidence:.2f}, risk={self.risk_level})"


class ConfidenceEngine:
    """Global confidence calculation engine."""

    # Factor weights for confidence calculation
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "data_quality": 0.25,
        "source_reliability": 0.20,
        "sample_size": 0.15,
        "consistency": 0.15,
        "freshness": 0.10,
        "diversity": 0.10,
        "corroboration": 0.05,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._weights = weights or dict(self.DEFAULT_WEIGHTS)

    def calculate(
        self,
        factors: Dict[str, float],
        evidence: Optional[List[str]] = None,
        risk_override: Optional[str] = None,
    ) -> ConfidenceResult:
        """Calculate confidence from multiple factors (each 0.0-1.0)."""
        weighted_sum = 0.0
        total_weight = 0.0
        reasons = []

        for factor, value in factors.items():
            value = max(0.0, min(1.0, value))
            weight = self._weights.get(factor, 0.05)
            weighted_sum += value * weight
            total_weight += weight
            if value >= 0.7:
                reasons.append(f"{factor} is strong ({value:.0%})")
            elif value < 0.3:
                reasons.append(f"{factor} is weak ({value:.0%})")

        confidence = round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.5

        # Determine risk level
        if risk_override:
            risk_level = risk_override
        elif confidence >= 0.85:
            risk_level = "VERY_LOW"
        elif confidence >= 0.70:
            risk_level = "LOW"
        elif confidence >= 0.50:
            risk_level = "MEDIUM"
        elif confidence >= 0.30:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return ConfidenceResult(
            confidence=confidence,
            reasons=reasons,
            risk_level=risk_level,
            evidence=evidence or [],
        )

    def aggregate(self, results: List[ConfidenceResult]) -> ConfidenceResult:
        """Aggregate multiple confidence results into one."""
        if not results:
            return ConfidenceResult(confidence=0.0, risk_level="CRITICAL")

        confidences = [r.confidence for r in results]
        avg_confidence = sum(confidences) / len(confidences)

        all_reasons = []
        all_evidence = []
        for r in results:
            all_reasons.extend(r.reasons)
            all_evidence.extend(r.evidence)

        # Aggregate risk: worst case wins
        risk_order = {level: i for i, level in enumerate(ConfidenceResult.RISK_LEVELS)}
        worst_risk = max(results, key=lambda r: risk_order.get(r.risk_level, 2))

        # If any result is CRITICAL, aggregate is at least HIGH
        if any(r.risk_level == "CRITICAL" for r in results):
            agg_risk = "HIGH"
        else:
            agg_risk = worst_risk.risk_level

        return ConfidenceResult(
            confidence=round(avg_confidence, 3),
            reasons=all_reasons[:10],
            risk_level=agg_risk,
            evidence=all_evidence[:10],
            metadata={"source_count": len(results)},
        )

    def from_evidence(self, evidence_list: List[str]) -> ConfidenceResult:
        """Create confidence from an evidence list (simple heuristic)."""
        if not evidence_list:
            return ConfidenceResult(confidence=0.1, risk_level="CRITICAL", reasons=["No evidence provided"])

        count = len(evidence_list)
        confidence = min(1.0, 0.3 + count * 0.1)
        risk_level = "LOW" if confidence >= 0.7 else "MEDIUM" if confidence >= 0.5 else "HIGH"

        return ConfidenceResult(
            confidence=round(confidence, 3),
            reasons=[f"{count} evidence items collected"],
            risk_level=risk_level,
            evidence=evidence_list,
        )

    def compare(self, a: ConfidenceResult, b: ConfidenceResult) -> str:
        """Compare two confidence results. Returns 'A', 'B', or 'EQUAL'."""
        if a.confidence > b.confidence:
            return "A"
        elif b.confidence > a.confidence:
            return "B"
        return "EQUAL"
