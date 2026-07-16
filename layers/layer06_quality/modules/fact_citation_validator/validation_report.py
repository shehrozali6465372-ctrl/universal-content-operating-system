"""Validation Report — Result models for fact and citation validation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ClaimValidation:
    """Validation result for a single claim."""

    __slots__ = (
        "claim_text", "claim_type", "status", "confidence",
        "evidence_count", "support_ratio", "has_citation",
        "issues",
    )

    VALID_STATUSES = ("verified", "partially_verified", "unverified", "unsupported", "contradicted")

    def __init__(
        self,
        claim_text: str = "",
        claim_type: str = "general",
        status: str = "unverified",
        confidence: float = 0.0,
        evidence_count: int = 0,
        support_ratio: float = 0.0,
        has_citation: bool = False,
        issues: Optional[List[str]] = None,
    ) -> None:
        self.claim_text = claim_text
        self.claim_type = claim_type
        self.status = status if status in self.VALID_STATUSES else "unverified"
        self.confidence = max(0.0, min(1.0, confidence))
        self.evidence_count = evidence_count
        self.support_ratio = max(0.0, min(1.0, support_ratio))
        self.has_citation = has_citation
        self.issues: List[str] = issues or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_text": self.claim_text[:200],
            "claim_type": self.claim_type,
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
            "support_ratio": round(self.support_ratio, 3),
            "has_citation": self.has_citation,
            "issues": self.issues,
        }


class CitationValidation:
    """Validation result for a single citation."""

    __slots__ = (
        "citation_text", "source", "is_valid", "has_url",
        "reliability_score", "issues",
    )

    def __init__(
        self,
        citation_text: str = "",
        source: str = "",
        is_valid: bool = True,
        has_url: bool = False,
        reliability_score: float = 0.5,
        issues: Optional[List[str]] = None,
    ) -> None:
        self.citation_text = citation_text
        self.source = source
        self.is_valid = is_valid
        self.has_url = has_url
        self.reliability_score = max(0.0, min(1.0, reliability_score))
        self.issues: List[str] = issues or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_text": self.citation_text[:200],
            "source": self.source,
            "is_valid": self.is_valid,
            "has_url": self.has_url,
            "reliability_score": round(self.reliability_score, 3),
            "issues": self.issues,
        }


class NumericalAccuracy:
    """Validation result for numerical consistency."""

    __slots__ = ("number_text", "category", "is_consistent", "issues")

    def __init__(
        self,
        number_text: str = "",
        category: str = "general",
        is_consistent: bool = True,
        issues: Optional[List[str]] = None,
    ) -> None:
        self.number_text = number_text
        self.category = category
        self.is_consistent = is_consistent
        self.issues: List[str] = issues or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number_text": self.number_text,
            "category": self.category,
            "is_consistent": self.is_consistent,
            "issues": self.issues,
        }


class ValidationReport:
    """Complete validation report for content."""

    __slots__ = (
        "overall_status", "overall_score", "claim_validations",
        "citation_validations", "numerical_checks", "issues",
        "statistics",
    )

    def __init__(self) -> None:
        self.overall_status = "unreviewed"
        self.overall_score = 0.0
        self.claim_validations: List[ClaimValidation] = []
        self.citation_validations: List[CitationValidation] = []
        self.numerical_checks: List[NumericalAccuracy] = []
        self.issues: List[str] = []
        self.statistics: Dict[str, Any] = {}

    def add_claim(self, cv: ClaimValidation) -> None:
        self.claim_validations.append(cv)

    def add_citation(self, cv: CitationValidation) -> None:
        self.citation_validations.append(cv)

    def add_numerical(self, na: NumericalAccuracy) -> None:
        self.numerical_checks.append(na)

    def compute_overall(self) -> None:
        """Compute overall status and score from individual checks."""
        all_claims = self.claim_validations
        if not all_claims:
            self.overall_score = 0.5
            self.overall_status = "no_claims"
            self.statistics = {"claim_count": 0, "citation_count": len(self.citation_validations)}
            return

        verified = sum(1 for c in all_claims if c.status == "verified")
        partial = sum(1 for c in all_claims if c.status == "partially_verified")
        unsupported = sum(1 for c in all_claims if c.status == "unsupported")
        contradicted = sum(1 for c in all_claims if c.status == "contradicted")

        n = len(all_claims)
        claim_score = (verified * 1.0 + partial * 0.6 + (n - verified - partial - unsupported - contradicted) * 0.4) / n

        cit_issues = sum(1 for c in self.citation_validations if not c.is_valid)
        cit_score = max(0.0, 1.0 - (cit_issues / max(1, len(self.citation_validations))))

        num_issues = sum(1 for n in self.numerical_checks if not n.is_consistent)
        num_score = max(0.0, 1.0 - (num_issues / max(1, len(self.numerical_checks))))

        self.overall_score = round(claim_score * 0.6 + cit_score * 0.25 + num_score * 0.15, 3)

        if contradicted > 0:
            self.overall_status = "contradicted"
        elif unsupported > n * 0.5:
            self.overall_status = "mostly_unsupported"
        elif verified >= n * 0.7:
            self.overall_status = "verified"
        elif verified >= n * 0.4:
            self.overall_status = "partially_verified"
        else:
            self.overall_status = "needs_review"

        self.statistics = {
            "claim_count": n,
            "verified": verified,
            "partially_verified": partial,
            "unsupported": unsupported,
            "contradicted": contradicted,
            "citation_count": len(self.citation_validations),
            "valid_citations": sum(1 for c in self.citation_validations if c.is_valid),
            "numerical_checks": len(self.numerical_checks),
            "consistent_numbers": sum(1 for n in self.numerical_checks if n.is_consistent),
            "overall_score": self.overall_score,
            "overall_status": self.overall_status,
        }

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        return {
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "claim_validations": [c.to_dict() for c in self.claim_validations],
            "citation_validations": [c.to_dict() for c in self.citation_validations],
            "numerical_checks": [n.to_dict() for n in self.numerical_checks],
            "issues": self.issues,
            "statistics": self.statistics,
        }
