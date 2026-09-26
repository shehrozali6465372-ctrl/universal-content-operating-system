"""Fact and citation validation for Layer 06.

The validator distinguishes citation presence/format from factual verification.
A syntactically valid citation is not treated as proof of a claim.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.fact_citation_validator.claim_parser import ClaimParser
from layers.layer06_quality.modules.fact_citation_validator.citation_checker import CitationChecker
from layers.layer06_quality.modules.fact_citation_validator.unsupported_claim_detector import (
    UnsupportedClaimDetector,
)
from layers.layer06_quality.modules.fact_citation_validator.numerical_accuracy_checker import (
    NumericalAccuracyChecker,
)
from layers.layer06_quality.modules.fact_citation_validator.validation_report import (
    ClaimValidation,
    ValidationReport,
)


class FactValidator:
    """Validate claims, citations, evidence references, and numerical consistency."""

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
        """Validate content without falsely upgrading citation presence to proof."""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")

        report = ValidationReport()
        start_time = time.monotonic()
        parsed_claims = self.claim_parser.parse(content)
        citation_validations = self.citation_checker.check_content_citations(
            parsed_claims, evidence_texts,
        )

        for index, pc in enumerate(parsed_claims):
            citation = citation_validations[index]
            cv = ClaimValidation(
                claim_text=pc.claim.text,
                claim_type=pc.claim.claim_type,
                has_citation=pc.has_inline_citation,
            )
            cv.confidence = pc.claim.confidence

            if not pc.has_inline_citation:
                cv.status = "unsupported"
                cv.issues.append("no_inline_citation")
            elif not citation.is_valid:
                cv.status = "unverified"
                cv.issues.extend(citation.issues or ["citation_invalid"])
            elif self._claim_has_exact_evidence(pc.claim.text, evidence_texts):
                cv.status = "verified"
                cv.evidence_count = 1
                cv.support_ratio = 1.0
            else:
                # A valid citation proves citation structure/reliability, not
                # the truth of the underlying claim.
                cv.status = "partially_verified"
                cv.evidence_count = 0
                cv.support_ratio = 0.0
                cv.issues.append("source_content_not_verified")
            report.add_claim(cv)
            report.add_citation(citation)

        unsupported = self.unsupported_detector.detect(parsed_claims, evidence_texts)
        for item in unsupported:
            report.issues.append(
                f"unsupported_{item.severity}: {item.claim_text[:100]}"
            )

        for numerical in self.numerical_checker.check(content):
            report.add_numerical(numerical)

        report.compute_overall()
        report.statistics["validation_time_ms"] = round(
            (time.monotonic() - start_time) * 1000, 2,
        )
        report.statistics["content_length"] = len(content)
        self._validate_count += 1
        return report

    @staticmethod
    def _claim_has_exact_evidence(
        claim_text: str,
        evidence_texts: Optional[List[Dict[str, str]]],
    ) -> bool:
        """Return true only when the complete normalized claim is in evidence."""
        if not evidence_texts:
            return False
        normalized_claim = re.sub(r"\s+", " ", claim_text).strip().lower()
        if not normalized_claim:
            return False
        for evidence in evidence_texts:
            if not isinstance(evidence, dict):
                continue
            text = evidence.get("text", "")
            normalized_text = re.sub(r"\s+", " ", text).strip().lower()
            if normalized_claim in normalized_text:
                return True
        return False

    def validate_batch(
        self,
        contents: List[str],
        evidence_texts: Optional[List[Dict[str, str]]] = None,
    ) -> List[ValidationReport]:
        """Validate multiple content pieces."""
        return [self.validate(content, evidence_texts) for content in contents]

    def validate_quick(self, content: str) -> Dict[str, Any]:
        """Validate and return a compact summary."""
        report = self.validate(content)
        return {
            "overall_status": report.overall_status,
            "overall_score": report.overall_score,
            "claim_count": report.statistics.get("claim_count", 0),
            "unsupported_count": report.statistics.get("unsupported", 0),
            "citation_count": report.statistics.get("citation_count", 0),
            "valid_citations": report.statistics.get("valid_citations", 0),
            "numerical_issues": sum(
                1 for item in report.numerical_checks if not item.is_consistent
            ),
        }

    @property
    def validate_count(self) -> int:
        return self._validate_count
