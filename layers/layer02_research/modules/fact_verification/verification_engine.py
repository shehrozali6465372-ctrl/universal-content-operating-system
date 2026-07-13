"""
Verification Engine
Layer 2: Research Engine — Module 6

Core verification logic combining all sub-components:
- Full verification pipeline
- Multi-evidence verification
- Confidence-weighted results
- Verification status determination
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.fact_verification.claim_extractor import Claim
from layers.layer02_research.modules.fact_verification.evidence_matcher import EvidenceMatcher, EvidenceMatch
from layers.layer02_research.modules.fact_verification.source_validator import SourceValidator, SourceValidation
from layers.layer02_research.modules.fact_verification.contradiction_detector import ContradictionDetector, Contradiction
from layers.layer02_research.modules.fact_verification.citation_builder import CitationBuilder, Citation
from layers.layer02_research.shared.confidence_engine import ConfidenceEngine, ConfidenceResult


VERIFICATION_STATUSES = ["verified", "partially_verified", "unverified", "contradicted", "insufficient_data"]


class VerificationResult:
    """Result of verifying a single claim."""

    __slots__ = (
        "claim", "status", "confidence_result",
        "evidence_matches", "contradictions", "citations",
        "source_validations", "support_ratio",
    )

    def __init__(self, claim: Claim):
        self.claim = claim
        self.status = "unverified"
        self.confidence_result = ConfidenceResult()
        self.evidence_matches: List[EvidenceMatch] = []
        self.contradictions: List[Contradiction] = []
        self.citations: List[Citation] = []
        self.source_validations: List[SourceValidation] = []
        self.support_ratio = 0.0

    def to_dict(self) -> dict:
        return {
            "claim": self.claim.to_dict(),
            "status": self.status,
            "confidence": self.confidence_result.confidence,
            "risk_level": self.confidence_result.risk_level,
            "evidence_count": len(self.evidence_matches),
            "support_ratio": self.support_ratio,
            "contradiction_count": len(self.contradictions),
            "citation_count": len(self.citations),
            "evidence": [m.to_dict() for m in self.evidence_matches[:5]],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "reasons": self.confidence_result.reasons,
            "verification_evidence": self.confidence_result.evidence,
        }


class VerificationEngine:
    """Core verification pipeline."""

    def __init__(
        self,
        evidence_matcher: Optional[EvidenceMatcher] = None,
        source_validator: Optional[SourceValidator] = None,
        contradiction_detector: Optional[ContradictionDetector] = None,
        citation_builder: Optional[CitationBuilder] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
    ):
        self.evidence_matcher = evidence_matcher or EvidenceMatcher()
        self.source_validator = source_validator or SourceValidator()
        self.contradiction_detector = contradiction_detector or ContradictionDetector()
        self.citation_builder = citation_builder or CitationBuilder()
        self.confidence_engine = confidence_engine or ConfidenceEngine()

    def verify(
        self,
        claim: Claim,
        evidence_texts: List[Dict[str, str]],
    ) -> VerificationResult:
        """Full verification pipeline for a single claim."""
        result = VerificationResult(claim)

        # Step 1: Match evidence
        matches = self.evidence_matcher.match(claim, evidence_texts)
        result.evidence_matches = matches

        # Step 2: Validate sources
        sources = list(set(m.evidence_source for m in matches if m.evidence_source))
        result.source_validations = self.source_validator.validate_batch(sources)

        # Step 3: Check contradictions
        ev_texts = [m.evidence_text for m in matches]
        result.contradictions = self.contradiction_detector.detect_batch(claim.text, ev_texts)

        # Step 4: Build citations
        evidence_entries = [
            {"source": m.evidence_source, "title": "", "source_url": "", "credibility_score": 0.7}
            for m in matches[:5]
        ]
        result.citations = self.citation_builder.build_from_evidence(evidence_entries)

        # Step 5: Calculate support ratio
        if matches:
            supporting = sum(1 for m in matches if m.supports)
            result.support_ratio = round(supporting / len(matches), 3)

        # Step 6: Determine status
        result.status = self._determine_status(result)

        # Step 7: Build confidence
        result.confidence_result = self._build_confidence(result)

        return result

    def verify_batch(
        self,
        claims: List[Claim],
        evidence_texts: List[Dict[str, str]],
    ) -> List[VerificationResult]:
        """Verify multiple claims."""
        return [self.verify(claim, evidence_texts) for claim in claims]

    def _determine_status(self, result: VerificationResult) -> str:
        """Determine verification status."""
        if not result.evidence_matches:
            return "insufficient_data"
        if result.contradictions and any(c.severity > 0.5 for c in result.contradictions):
            return "contradicted"
        if result.support_ratio >= 0.7 and len(result.evidence_matches) >= 2:
            return "verified"
        if result.support_ratio >= 0.4:
            return "partially_verified"
        return "unverified"

    def _build_confidence(self, result: VerificationResult) -> ConfidenceResult:
        """Build confidence result from verification data."""
        factors = {}

        # Evidence quality
        if result.evidence_matches:
            avg_sim = sum(m.similarity_score for m in result.evidence_matches) / len(result.evidence_matches)
            factors["data_quality"] = avg_sim
        else:
            factors["data_quality"] = 0.1

        # Source reliability
        if result.source_validations:
            avg_cred = sum(s.credibility_score for s in result.source_validations) / len(result.source_validations)
            factors["source_reliability"] = avg_cred
        else:
            factors["source_reliability"] = 0.2

        # Sample size
        factors["sample_size"] = min(1.0, len(result.evidence_matches) / 5)

        # Consistency (low contradictions = high consistency)
        contra_severity = self.contradiction_detector.get_contradiction_severity(result.contradictions)
        factors["consistency"] = max(0.0, 1.0 - contra_severity)

        # Evidence points
        evidence = []
        if result.support_ratio >= 0.7:
            evidence.append(f"Strong support from {len(result.evidence_matches)} sources")
        if result.contradictions:
            evidence.append(f"{len(result.contradictions)} contradiction(s) detected")
        if result.source_validations:
            credible = sum(1 for s in result.source_validations if s.credibility_score >= 0.7)
            if credible:
                evidence.append(f"{credible} credible source(s)")

        return self.confidence_engine.calculate(factors, evidence=evidence)
