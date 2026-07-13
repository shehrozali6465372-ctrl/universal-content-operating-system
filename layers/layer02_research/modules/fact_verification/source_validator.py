"""
Source Validator
Layer 2: Research Engine — Module 6

Validates credibility of sources:
- Source reputation scoring
- Cross-source corroboration
- Source diversity check
- Authority level assessment
"""

from typing import Dict, List, Optional


class SourceValidation:
    """Validation result for a source."""

    __slots__ = (
        "source_name", "credibility_score", "authority_level",
        "corroboration_count", "is_primary_source",
        "has_citation", "freshness_penalty", "flags",
    )

    AUTHORITY_LEVELS = ["peer_reviewed", "official", "reputable", "blog", "unknown"]

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.credibility_score = 0.5
        self.authority_level = "unknown"
        self.corroboration_count = 0
        self.is_primary_source = False
        self.has_citation = False
        self.freshness_penalty = 0.0
        self.flags: List[str] = []

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "credibility_score": self.credibility_score,
            "authority_level": self.authority_level,
            "corroboration_count": self.corroboration_count,
            "is_primary_source": self.is_primary_source,
            "has_citation": self.has_citation,
            "freshness_penalty": self.freshness_penalty,
            "flags": self.flags,
        }


# Known high-credibility source patterns
HIGH_CREDIBILITY = {
    "reuters": 0.95, "associated press": 0.95, "bbc": 0.9,
    "nytimes": 0.9, "washington post": 0.9, "guardian": 0.85,
    "nature": 0.95, "science": 0.95, "ieee": 0.9,
    "harvard": 0.9, "stanford": 0.9, "mit": 0.9,
    "github": 0.7, "stackoverflow": 0.7,
}

MEDIUM_CREDIBILITY = {
    "medium": 0.6, "substack": 0.6, "reddit": 0.5,
    "quora": 0.4, "yahoo": 0.5,
}


class SourceValidator:
    """Validate source credibility."""

    def __init__(self, custom_scores: Optional[Dict[str, float]] = None):
        self._scores: Dict[str, float] = dict(HIGH_CREDIBILITY)
        self._scores.update(MEDIUM_CREDIBILITY)
        if custom_scores:
            self._scores.update(custom_scores)

    def validate(self, source_name: str) -> SourceValidation:
        """Validate a single source."""
        sv = SourceValidation(source_name)
        normalized = source_name.lower().strip()

        # Check known sources
        for known, score in self._scores.items():
            if known in normalized or normalized in known:
                sv.credibility_score = score
                if score >= 0.8:
                    sv.authority_level = "reputable"
                elif score >= 0.6:
                    sv.authority_level = "blog"
                break

        # Check authority indicators
        if any(kw in normalized for kw in [".edu", ".gov", ".org", "university", "journal"]):
            sv.authority_level = "official"
            sv.credibility_score = max(sv.credibility_score, 0.85)
        if any(kw in normalized for kw in ["research", "study", "paper", "journal"]):
            sv.is_primary_source = True
            sv.credibility_score = max(sv.credibility_score, 0.8)
        if any(kw in normalized for kw in ["cited", "reference", "source", "according to"]):
            sv.has_citation = True

        # Flags
        if sv.credibility_score < 0.3:
            sv.flags.append("low_credibility")
        if sv.authority_level == "unknown":
            sv.flags.append("unverified_source")

        return sv

    def validate_batch(self, source_names: List[str]) -> List[SourceValidation]:
        """Validate multiple sources."""
        return [self.validate(name) for name in source_names]

    def cross_corroborate(
        self, validations: List[SourceValidation], min_sources: int = 2
    ) -> Dict[str, any]:
        """Check if sources corroborate each other."""
        unique_sources = set(v.source_name for v in validations)
        credible = [v for v in validations if v.credibility_score >= 0.6]
        primary = [v for v in validations if v.is_primary_source]

        avg_credibility = (
            sum(v.credibility_score for v in validations) / len(validations)
            if validations else 0.0
        )

        is_corroborated = len(credible) >= min_sources
        has_diversity = len(unique_sources) >= 2

        return {
            "total_sources": len(unique_sources),
            "credible_sources": len(credible),
            "primary_sources": len(primary),
            "avg_credibility": round(avg_credibility, 3),
            "is_corroborated": is_corroborated,
            "has_diversity": has_diversity,
            "confidence_boost": round(
                min(0.3, len(credible) * 0.1 + (0.1 if has_diversity else 0)), 3
            ),
        }

    def get_source_score(self, source_name: str) -> float:
        """Quick credibility lookup."""
        normalized = source_name.lower().strip()
        for known, score in self._scores.items():
            if known in normalized:
                return score
        return 0.4  # Default for unknown sources

    def register_source(self, name: str, credibility: float):
        """Register a custom source credibility score."""
        self._scores[name.lower().strip()] = max(0.0, min(1.0, credibility))
