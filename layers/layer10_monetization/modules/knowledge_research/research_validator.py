"""ResearchValidator — Validate research quality."""
from __future__ import annotations
from typing import Any, Dict, List


class ValidationResult:
    """Result of research validation."""

    __slots__ = ("is_valid", "score", "issues", "warnings")

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.score: float = 1.0
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {"is_valid": self.is_valid, "score": round(self.score, 3),
                "issues": self.issues, "warnings": self.warnings}


class ResearchValidator:
    """Validate research quality, freshness, and reliability."""

    def __init__(self, min_confidence: float = 0.3) -> None:
        self._min_confidence = min_confidence
        self._validations: List[ValidationResult] = []

    def validate(self, research_data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        confidence = research_data.get("confidence", 0.5)
        source_count = research_data.get("source_count", 0)

        if confidence < self._min_confidence:
            result.issues.append(f"Low confidence: {confidence}")
            result.score *= 0.5

        if source_count < 1:
            result.warnings.append("No sources provided")

        freshness = research_data.get("freshness_hours", 0)
        if freshness > 168:
            result.warnings.append(f"Stale data: {freshness}h old")

        result.is_valid = len(result.issues) == 0
        result.score = max(0.0, result.score)
        self._validations.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._validations),
                "valid": sum(1 for v in self._validations if v.is_valid)}
