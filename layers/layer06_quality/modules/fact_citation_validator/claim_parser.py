"""Claim Parser — Extract claims from written content for validation.

Reuses Layer 2's ClaimExtractor for claim identification, and adds
content-level analysis (inline citations, attribution patterns).
"""
from __future__ import annotations
import re
from typing import List, Tuple

from layers.layer02_research.modules.fact_verification.claim_extractor import Claim, ClaimExtractor


INLINE_CITATION_PATTERNS = [
    re.compile(r'\((?:[^)]*?\d{4}[^)]*?)\)'),           # (Author, 2024) or (Smith et al., 2023)
    re.compile(r'\[(?:[^\]]*?\d+(?:,\s*\d+)*)\]'),       # [1] or [1,2,3]
    re.compile(r'(?:source|according\s+to)\s+[:.]?\s*\w+', re.IGNORECASE),  # source: XYZ
    re.compile(r'(?:study|report|survey)\s+(?:by|from)\s+\w+', re.IGNORECASE),
]


class ParsedClaim:
    """A claim extracted from written content with citation context."""

    __slots__ = (
        "claim", "has_inline_citation", "citation_context",
        "attribution_pattern", "position",
    )

    def __init__(
        self,
        claim: Claim,
        has_inline_citation: bool = False,
        citation_context: str = "",
        attribution_pattern: str = "",
        position: int = 0,
    ) -> None:
        self.claim = claim
        self.has_inline_citation = has_inline_citation
        self.citation_context = citation_context
        self.attribution_pattern = attribution_pattern
        self.position = position

    def to_dict(self) -> dict:
        return {
            "claim": self.claim.to_dict(),
            "has_inline_citation": self.has_inline_citation,
            "citation_context": self.citation_context,
            "attribution_pattern": self.attribution_pattern,
            "position": self.position,
        }


class ClaimParser:
    """Parse and enrich claims from written content."""

    def __init__(
        self,
        min_claim_length: int = 10,
        max_claims: int = 20,
    ) -> None:
        self._extractor = ClaimExtractor(
            min_claim_length=min_claim_length,
            max_claims=max_claims,
        )
        self._parse_count = 0

    def parse(self, text: str) -> List[ParsedClaim]:
        """Parse claims from content text, enriching with citation info."""
        claims = self._extractor.extract(text)
        parsed: List[ParsedClaim] = []
        for claim in claims:
            ctx, pattern = self._find_citation_context(text, claim)
            pc = ParsedClaim(
                claim=claim,
                has_inline_citation=bool(pattern),
                citation_context=ctx,
                attribution_pattern=pattern,
                position=claim.position,
            )
            parsed.append(pc)
        self._parse_count += 1
        return parsed

    def parse_statistical(self, text: str) -> List[ParsedClaim]:
        """Parse only statistical claims."""
        return [p for p in self.parse(text) if p.claim.claim_type == "statistical"]

    def _find_citation_context(
        self, text: str, claim: Claim,
    ) -> Tuple[str, str]:
        """Find citation context near a claim's position."""
        if claim.position < 0:
            return "", ""
        window_start = max(0, claim.position)
        window_end = min(len(text), claim.position + len(claim.text) + 80)
        window = text[window_start:window_end]

        for pattern in INLINE_CITATION_PATTERNS:
            match = pattern.search(window)
            if match:
                return match.group(0), pattern.pattern[:30]
        return "", ""

    def get_claims_without_citations(
        self, parsed: List[ParsedClaim],
    ) -> List[ParsedClaim]:
        """Return claims that have no inline citation."""
        return [p for p in parsed if not p.has_inline_citation]

    @property
    def parse_count(self) -> int:
        return self._parse_count
