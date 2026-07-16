"""Quality Grader — Convert numeric scores to letter grades."""
from __future__ import annotations
from typing import List, Optional, Tuple


GRADE_THRESHOLDS: List[Tuple[float, str]] = [
    (97, "A+"), (93, "A"), (90, "A-"),
    (87, "B+"), (83, "B"), (80, "B-"),
    (77, "C+"), (73, "C"), (70, "C-"),
    (60, "D"), (0, "F"),
]


class QualityGrader:
    """Convert numeric scores to letter grades."""

    def __init__(self, custom_thresholds: Optional[List[Tuple[float, str]]] = None) -> None:
        self._thresholds = custom_thresholds or GRADE_THRESHOLDS

    def grade(self, score: float) -> str:
        """Convert numeric score (0-100) to letter grade."""
        for threshold, letter in self._thresholds:
            if score >= threshold:
                return letter
        return "F"

    def grade_description(self, letter: str) -> str:
        """Get description for a letter grade."""
        descriptions = {
            "A+": "Exceptional — exceeds all quality standards",
            "A": "Excellent — meets all quality standards",
            "A-": "Very Good — meets most standards with minor gaps",
            "B+": "Good — solid quality with room for improvement",
            "B": "Above Average — acceptable quality",
            "B-": "Average — meets minimum standards",
            "C+": "Below Average — needs improvement",
            "C": "Poor — significant improvement needed",
            "C-": "Very Poor — major quality issues",
            "D": "Failing — does not meet standards",
            "F": "Unacceptable — critical quality failures",
        }
        return descriptions.get(letter, "Unknown grade")

    def is_passing(self, letter: str) -> bool:
        """Check if a grade is passing (C- or above)."""
        passing = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-"}
        return letter in passing

    def is_publish_ready(self, letter: str) -> bool:
        """Check if content is publish-ready (B- or above)."""
        ready = {"A+", "A", "A-", "B+", "B", "B-"}
        return letter in ready
