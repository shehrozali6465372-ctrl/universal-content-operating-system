"""Originality Report — Result models for plagiarism and originality checking."""
from __future__ import annotations
from typing import Any, Dict, List


class FlaggedSegment:
    """A segment of content flagged for potential plagiarism."""

    __slots__ = (
        "text", "start_pos", "end_pos", "match_type",
        "similarity_score", "source", "severity", "suggestion",
    )

    def __init__(
        self,
        text: str = "",
        start_pos: int = 0,
        end_pos: int = 0,
        match_type: str = "unknown",
        similarity_score: float = 0.0,
        source: str = "",
        severity: str = "low",
        suggestion: str = "",
    ) -> None:
        self.text = text
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.match_type = match_type
        self.similarity_score = max(0.0, min(1.0, similarity_score))
        self.source = source
        self.severity = severity
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:200],
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "match_type": self.match_type,
            "similarity_score": round(self.similarity_score, 3),
            "source": self.source,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


class SelfPlagiarismMatch:
    """A match against previously published content."""

    __slots__ = (
        "current_text", "previous_text", "previous_source",
        "similarity_score", "match_type",
    )

    def __init__(
        self,
        current_text: str = "",
        previous_text: str = "",
        previous_source: str = "",
        similarity_score: float = 0.0,
        match_type: str = "exact",
    ) -> None:
        self.current_text = current_text
        self.previous_text = previous_text
        self.previous_source = previous_source
        self.similarity_score = max(0.0, min(1.0, similarity_score))
        self.match_type = match_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_text": self.current_text[:200],
            "previous_text": self.previous_text[:200],
            "previous_source": self.previous_source,
            "similarity_score": round(self.similarity_score, 3),
            "match_type": self.match_type,
        }


class OriginalityReport:
    """Complete originality report for content."""

    __slots__ = (
        "overall_originality_score", "is_original",
        "flagged_segments", "self_plagiarism_matches",
        "phrase_duplicates", "statistics", "issues",
    )

    def __init__(self) -> None:
        self.overall_originality_score = 1.0
        self.is_original = True
        self.flagged_segments: List[FlaggedSegment] = []
        self.self_plagiarism_matches: List[SelfPlagiarismMatch] = []
        self.phrase_duplicates: List[Dict[str, Any]] = []
        self.statistics: Dict[str, Any] = {}
        self.issues: List[str] = []

    def compute_overall(self) -> None:
        """Compute overall originality from all checks."""
        total_segments = len(self.flagged_segments)
        self_matches = len(self.self_plagiarism_matches)
        phrase_dups = len(self.phrase_duplicates)

        # Deduction based on flags
        high_flags = sum(1 for s in self.flagged_segments if s.severity == "high")
        medium_flags = sum(1 for s in self.flagged_segments if s.severity == "medium")
        low_flags = sum(1 for s in self.flagged_segments if s.severity == "low")

        deduction = high_flags * 0.15 + medium_flags * 0.07 + low_flags * 0.02
        self_plagiarism_deduction = self_matches * 0.1

        self.overall_originality_score = max(0.0, 1.0 - deduction - self_plagiarism_deduction)
        self.is_original = self.overall_originality_score >= 0.7

        self.statistics = {
            "total_flagged_segments": total_segments,
            "high_severity_flags": high_flags,
            "medium_severity_flags": medium_flags,
            "low_severity_flags": low_flags,
            "self_plagiarism_matches": self_matches,
            "phrase_duplicates": phrase_dups,
            "overall_originality_score": round(self.overall_originality_score, 3),
            "is_original": self.is_original,
        }

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        return {
            "overall_originality_score": self.overall_originality_score,
            "is_original": self.is_original,
            "flagged_segments": [s.to_dict() for s in self.flagged_segments],
            "self_plagiarism_matches": [m.to_dict() for m in self.self_plagiarism_matches],
            "phrase_duplicates": self.phrase_duplicates,
            "statistics": self.statistics,
            "issues": self.issues,
        }
