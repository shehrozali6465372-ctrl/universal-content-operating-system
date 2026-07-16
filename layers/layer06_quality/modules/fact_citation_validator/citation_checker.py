"""Citation Checker — Validate citation completeness and format.

Checks that:
- Claims with citations have valid format
- Sources are mentioned
- Citations have supporting data
- Citation style consistency
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional

from layers.layer06_quality.modules.fact_citation_validator.claim_parser import ParsedClaim
from layers.layer06_quality.modules.fact_citation_validator.validation_report import CitationValidation


CITATION_FORMAT_PATTERNS = {
    "author_year": re.compile(r'\(\w+(?:\s+(?:et\s+al\.?|and\s+\w+))?,?\s*\d{4}\)'),
    "numbered": re.compile(r'\[\d+(?:,\s*\d+)*\]'),
    "inline_text": re.compile(r'(?:according\s+to|as\s+reported\s+by|cited\s+by)\s+\w+', re.IGNORECASE),
    "footnote_style": re.compile(r'\w+\s*\d{4}(?:,\s*p\.?\s*\d+)?'),
}

KNOWN_CREDIBLE_SOURCES = {
    "google scholar", "pubmed", "reuters", "bbc", "cnbc", "forbes",
    "harvard", "mit", "stanford", "oxford", "cambridge", "ieee",
    "acm", "nature", "science", "the lancet", "new england journal",
    "world bank", "imf", "who", "un", "oecd", "bureau of labor",
}

UNRELIABLE_SOURCE_PATTERNS = [
    re.compile(r'(?:wikipedia|reddit|quora|yahoo\s+answers)', re.IGNORECASE),
    re.compile(r'(?:personal\s+blog|medium\.com|wordpress\.com)', re.IGNORECASE),
]


class CitationCheck:
    """Detailed check result for a single citation."""

    __slots__ = ("citation_text", "source", "format_valid", "has_url",
                 "reliability", "issues")

    def __init__(self, citation_text: str = "") -> None:
        self.citation_text = citation_text
        self.source = ""
        self.format_valid = True
        self.has_url = False
        self.reliability = "unknown"
        self.issues: List[str] = []

    def to_dict(self) -> dict:
        return {
            "citation_text": self.citation_text[:200],
            "source": self.source,
            "format_valid": self.format_valid,
            "has_url": self.has_url,
            "reliability": self.reliability,
            "issues": self.issues,
        }


class CitationChecker:
    """Validate citation quality and completeness."""

    def __init__(self) -> None:
        self._check_count = 0

    def check_inline_citation(self, citation_text: str) -> CitationCheck:
        """Check a single inline citation."""
        check = CitationCheck(citation_text)

        # Extract source
        check.source = self._extract_source(citation_text)

        # Check format
        check.format_valid = self._validate_format(citation_text)

        # Check URL
        check.has_url = "http" in citation_text.lower() or "www." in citation_text.lower()

        # Reliability assessment
        check.reliability = self._assess_reliability(check.source, citation_text)

        # Collect issues
        if not check.format_valid:
            check.issues.append("citation_format_invalid")
        if not check.source:
            check.issues.append("no_source_detected")
        if not check.has_url:
            check.issues.append("no_url_provided")
        if check.reliability == "low":
            check.issues.append("low_reliability_source")

        self._check_count += 1
        return check

    def check_batch(self, citations: List[str]) -> List[CitationCheck]:
        """Check multiple citations."""
        return [self.check_inline_citation(c) for c in citations]

    def check_content_citations(
        self, parsed_claims: List[ParsedClaim], evidence_texts: Optional[List[Dict[str, str]]] = None,
    ) -> List[CitationValidation]:
        """Check citations across all parsed claims."""
        validations: List[CitationValidation] = []

        for pc in parsed_claims:
            if pc.has_inline_citation:
                check = self.check_inline_citation(pc.citation_context)
                validations.append(CitationValidation(
                    citation_text=check.citation_text,
                    source=check.source,
                    is_valid=check.format_valid and check.reliability != "low",
                    has_url=check.has_url,
                    reliability_score=0.9 if check.reliability == "high" else 0.6 if check.reliability == "medium" else 0.3,
                    issues=check.issues,
                ))
            else:
                validations.append(CitationValidation(
                    citation_text="",
                    source="",
                    is_valid=False,
                    has_url=False,
                    reliability_score=0.0,
                    issues=["no_inline_citation"],
                ))

        self._check_count += 1
        return validations

    def _validate_format(self, citation_text: str) -> bool:
        """Check if citation matches any known format."""
        for pattern in CITATION_FORMAT_PATTERNS.values():
            if pattern.search(citation_text):
                return True
        # Accept if it looks like a reasonable citation (has year-like pattern)
        return bool(re.search(r'\b\d{4}\b', citation_text))

    def _extract_source(self, citation_text: str) -> str:
        """Extract source name from citation text."""
        # Try known source patterns
        for source in KNOWN_CREDIBLE_SOURCES:
            if source in citation_text.lower():
                return source.title()
        # Try extracting capitalized phrases
        match = re.search(r'(?:by|from|according\s+to)\s+([A-Z][\w\s]+)', citation_text)
        if match:
            return match.group(1).strip()
        return ""

    def _assess_reliability(self, source: str, citation_text: str) -> str:
        """Assess reliability of citation source."""
        source_lower = source.lower()
        citation_lower = citation_text.lower()

        for pattern in UNRELIABLE_SOURCE_PATTERNS:
            if pattern.search(citation_text):
                return "low"

        for known in KNOWN_CREDIBLE_SOURCES:
            if known in source_lower or known in citation_lower:
                return "high"

        if source:
            return "medium"
        return "unknown"

    @property
    def check_count(self) -> int:
        return self._check_count
