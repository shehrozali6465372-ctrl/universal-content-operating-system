"""Unsupported Claim Detector — Identify claims lacking evidence or citations.

Detects:
- Claims without any citation
- Statistical claims without sources
- Causal claims without evidence
- Comparative claims without data
- Hedged claims (may reduce severity)
"""
from __future__ import annotations
from typing import Dict, List, Optional

from layers.layer02_research.modules.fact_verification.claim_extractor import Claim
from layers.layer06_quality.modules.fact_citation_validator.claim_parser import ParsedClaim


HEDGE_WORDS = {"might", "could", "possibly", "perhaps", "maybe", "seems", "appears", "likely"}
MODAL_WORDS = {"will", "should", "would", "can", "must"}
OPINION_MARKERS = {"think", "believe", "feel", "opinion", "argue", "suggest", "in_my_view"}


class UnsupportedClaim:
    """A claim that lacks sufficient support."""

    __slots__ = (
        "claim_text", "claim_type", "reason", "severity",
        "has_citation", "has_evidence", "is_hedged",
    )

    def __init__(
        self,
        claim_text: str = "",
        claim_type: str = "general",
        reason: str = "",
        severity: str = "medium",
        has_citation: bool = False,
        has_evidence: bool = False,
        is_hedged: bool = False,
    ) -> None:
        self.claim_text = claim_text
        self.claim_type = claim_type
        self.reason = reason
        self.severity = severity
        self.has_citation = has_citation
        self.has_evidence = has_evidence
        self.is_hedged = is_hedged

    def to_dict(self) -> dict:
        return {
            "claim_text": self.claim_text[:200],
            "claim_type": self.claim_type,
            "reason": self.reason,
            "severity": self.severity,
            "has_citation": self.has_citation,
            "has_evidence": self.has_evidence,
            "is_hedged": self.is_hedged,
        }


class UnsupportedClaimDetector:
    """Detect claims that lack sufficient evidence or citations."""

    def __init__(self) -> None:
        self._detection_count = 0
        self._min_severity_for_statistical = "high"
        self._min_severity_for_causal = "medium"

    def detect(
        self,
        parsed_claims: List[ParsedClaim],
        evidence_texts: Optional[List[Dict[str, str]]] = None,
    ) -> List[UnsupportedClaim]:
        """Detect unsupported claims in parsed content."""
        unsupported: List[UnsupportedClaim] = []

        for pc in parsed_claims:
            claim = pc.claim
            is_hedged = self._is_hedged(claim.text)

            if not pc.has_inline_citation:
                severity = self._determine_severity(claim, is_hedged)
                unsupported.append(UnsupportedClaim(
                    claim_text=claim.text,
                    claim_type=claim.claim_type,
                    reason="no_inline_citation",
                    severity=severity,
                    has_citation=False,
                    has_evidence=False,
                    is_hedged=is_hedged,
                ))
            elif claim.claim_type == "statistical" and not pc.has_inline_citation:
                unsupported.append(UnsupportedClaim(
                    claim_text=claim.text,
                    claim_type=claim.claim_type,
                    reason="statistical_claim_no_source",
                    severity="high",
                    has_citation=False,
                    has_evidence=False,
                    is_hedged=is_hedged,
                ))

        self._detection_count += 1
        return unsupported

    def detect_batch(
        self, content_batches: List[List[ParsedClaim]],
    ) -> List[List[UnsupportedClaim]]:
        """Detect unsupported claims in multiple content batches."""
        return [self.detect(batch) for batch in content_batches]

    def get_high_severity(
        self, unsupported: List[UnsupportedClaim],
    ) -> List[UnsupportedClaim]:
        """Return only high-severity unsupported claims."""
        return [u for u in unsupported if u.severity == "high"]

    def _is_hedged(self, text: str) -> bool:
        """Check if claim uses hedging language."""
        words = set(text.lower().split())
        return bool(words & HEDGE_WORDS)

    def _determine_severity(self, claim: Claim, is_hedged: bool) -> str:
        """Determine severity of missing citation."""
        if claim.claim_type == "statistical":
            return "high"
        if claim.claim_type == "causal":
            return "high"
        if claim.claim_type == "trend":
            return "medium"
        if is_hedged:
            return "low"
        if claim.confidence > 0.7:
            return "high"
        return "medium"

    @property
    def detection_count(self) -> int:
        return self._detection_count
