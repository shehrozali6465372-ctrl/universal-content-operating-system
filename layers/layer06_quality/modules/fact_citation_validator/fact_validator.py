"""Fact Validator — Core validation engine for written content.

Orchestrates:
- Claim parsing (from Layer 2)
- Citation checking
- Unsupported claim detection
- Numerical accuracy validation
- Produces ValidationReport
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.fact_citation_validator.claim_parser import ClaimParser
from layers.layer06_quality.modules.fact_citation_validator.citation_checker import CitationChecker
from layers.layer06_quality.modules.fact_citation_validator.unsupported_claim_detector import UnsupportedClaimDetector
from layers.layer06_quality.modules.fact_citation_validator.numerical_accuracy_checker import NumericalAccuracyChecker
from layers.layer06_quality.modules.fact_citation_validator.validation_report import (
    ClaimValidation, ValidationReport,
)


class FactValidator:
    """Orchestrates full fact and citation validation pipeline."""

    def __init__(
        self,
        claim_parser: Optional[ClaimParser] = None,
        citation_checker: Optional[CitationChecker] = None,
        unsupported_detector: Optional[UnsupportedClaimDetector] = None,
        numerical_checker: Optional[NumericalAccuracyChecker] = None,
    ) -> None:
        self.claim_parser = claim_parser or ClaimParser()
        self.citation_checker = citation_checker or CitationChecker()
        self.unsupported_detector = unsupported_detector or UnsupportedClaimDetector()
        self.numerical_checker = numerical_checker or NumericalAccuracyChecker()
        self._validate_count = 0

    def validate(
        self,
        content: str,
        evidence_texts: Optional[List[Dict[str, str]]] = None,
    ) -> ValidationReport:
        """Full validation pipeline for written content."""
        report = ValidationReport()
        start_time = time.time()

        # Step 1: Parse claims from content
        parsed_claims = self.claim_parser.parse(content)

        # Step 2: Check each claim's citation status
        for pc in parsed_claims:
            cv = ClaimValidation(
                claim_text=pc.claim.text,
                claim_type=pc.claim.claim_type,
                has_citation=pc.has_inline_citation,
            )
            cv.confidence = pc.claim.confidence
            if pc.has_inline_citation:
                cv.status = "verified"
                cv.evidence_count = 1
                cv.support_ratio = 0.8
            else:
                cv.status = "unsupported"
                cv.issues.append("no_inline_citation")
            report.add_claim(cv)

        # Step 3: Check citations
        citation_validations = self.citation_checker.check_content_citations(parsed_claims)
        for cv in citation_validations:
            report.add_citation(cv)

        # Step 4: Detect unsupported claims
        unsupported = self.unsupported_detector.detect(parsed_claims, evidence_texts)
        for u in unsupported:
            report.issues.append(f"unsupported_{u.severity}: {u.claim_text[:100]}")

        # Step 5: Numerical accuracy
        numerical_results = self.numerical_checker.check(content)
        for nr in numerical_results:
            report.add_numerical(nr)

        # Step 6: Compute overall
        report.compute_overall()

        elapsed = time.time() - start_time
        report.statistics["validation_time_ms"] = round(elapsed * 1000, 2)
        report.statistics["content_length"] = len(content)

        self._validate_count += 1
        return report

    def validate_batch(
        self,
        contents: List[str],
        evidence_texts: Optional[List[Dict[str, str]]] = None,
    ) -> List[ValidationReport]:
        """Validate multiple content pieces."""
        return [self.validate(c, evidence_texts) for c in contents]

    def validate_quick(self, content: str) -> Dict[str, Any]:
        """Quick validation returning summary dict."""
        report = self.validate(content)
        return {
            "overall_status": report.overall_status,
            "overall_score": report.overall_score,
            "claim_count": report.statistics.get("claim_count", 0),
            "unsupported_count": report.statistics.get("unsupported", 0),
            "citation_count": report.statistics.get("citation_count", 0),
            "valid_citations": report.statistics.get("valid_citations", 0),
            "numerical_issues": sum(1 for n in report.numerical_checks if not n.is_consistent),
        }

    @property
    def validate_count(self) -> int:
        return self._validate_count
