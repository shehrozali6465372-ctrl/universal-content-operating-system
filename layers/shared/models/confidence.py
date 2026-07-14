"""
Shared Confidence Model
Frozen interface — v1.0.0
"""

from typing import Dict, List, Optional


class ConfidenceResult:
    """Standardized confidence output for any decision across all layers."""

    __slots__ = ("confidence", "reasons", "risk_level", "evidence", "metadata")

    RISK_LEVELS = ("VERY_LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL")

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
            "reasons": list(self.reasons),
            "risk_level": self.risk_level,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConfidenceResult":
        return cls(
            confidence=data.get("confidence", 0.5),
            reasons=data.get("reasons", []),
            risk_level=data.get("risk_level", "MEDIUM"),
            evidence=data.get("evidence", []),
            metadata=data.get("metadata", {}),
        )

    def add_reason(self, reason: str):
        self.reasons.append(reason)

    def add_evidence(self, evidence: str):
        self.evidence.append(evidence)

    def is_trustworthy(self) -> bool:
        """Is this result trustworthy enough to act on?"""
        return self.confidence >= 0.7 and self.risk_level in ("VERY_LOW", "LOW", "MEDIUM")

    def __repr__(self) -> str:
        return f"ConfidenceResult(confidence={self.confidence:.2f}, risk={self.risk_level})"
