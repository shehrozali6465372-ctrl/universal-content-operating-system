"""Optimization Validator — Ensure optimized content passes quality checks."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class OptimizationValidationResult:
    """Result of validating optimized content."""

    __slots__ = ("is_valid", "quality_score", "safety_pass", "brand_pass",
                 "violations", "warnings", "overall_score")

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.quality_score: float = 1.0
        self.safety_pass: bool = True
        self.brand_pass: bool = True
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self.overall_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "quality_score": round(self.quality_score, 3),
            "safety_pass": self.safety_pass,
            "brand_pass": self.brand_pass,
            "violation_count": len(self.violations),
            "warning_count": len(self.warnings),
            "overall_score": round(self.overall_score, 3),
        }


class OptimizationValidator:
    """Validate that optimized content meets quality, safety, and brand standards."""

    UNSAFE_PATTERNS = ("hate", "violence", "discriminat", "harassment")

    def __init__(self) -> None:
        self._results: List[OptimizationValidationResult] = []

    def validate(self, content: str, min_quality: float = 0.3,
                 brand_terms: Optional[List[str]] = None,
                 forbidden_terms: Optional[List[str]] = None) -> OptimizationValidationResult:
        result = OptimizationValidationResult()
        result.quality_score = self._check_quality(content)
        result.safety_pass = self._check_safety(content)
        result.brand_pass = self._check_brand(content, brand_terms, forbidden_terms)
        result.violations = self._get_violations(content, forbidden_terms)
        result.warnings = self._get_warnings(content, min_quality)
        result.is_valid = result.safety_pass and result.brand_pass and result.quality_score >= min_quality
        result.overall_score = round(
            result.quality_score * 0.4 + (1.0 if result.safety_pass else 0.0) * 0.3 +
            (1.0 if result.brand_pass else 0.0) * 0.3, 3,
        )
        self._results.append(result)
        return result

    def _check_quality(self, content: str) -> float:
        if not content:
            return 0.0
        score = 0.5
        words = content.split()
        if len(words) >= 10:
            score += 0.2
        if len(words) >= 50:
            score += 0.1
        if content.count(".") + content.count("!") + content.count("?") >= 2:
            score += 0.2
        return round(min(1.0, score), 3)

    def _check_safety(self, content: str) -> bool:
        lower = content.lower()
        return not any(p in lower for p in self.UNSAFE_PATTERNS)

    def _check_brand(self, content: str, brand_terms: Optional[List[str]] = None,
                     forbidden_terms: Optional[List[str]] = None) -> bool:
        if forbidden_terms:
            lower = content.lower()
            for term in forbidden_terms:
                if term.lower() in lower:
                    return False
        return True

    def _get_violations(self, content: str, forbidden_terms: Optional[List[str]] = None) -> List[str]:
        violations = []
        lower = content.lower()
        if not self._check_safety(content):
            violations.append("Content contains unsafe patterns")
        if forbidden_terms:
            for term in forbidden_terms:
                if term.lower() in lower:
                    violations.append(f"Forbidden term: '{term}'")
        return violations

    def _get_warnings(self, content: str, min_quality: float) -> List[str]:
        warnings = []
        if self._check_quality(content) < min_quality:
            warnings.append("Quality below minimum threshold")
        if len(content.split()) < 10:
            warnings.append("Content may be too short")
        return warnings

    def get_results(self) -> List[OptimizationValidationResult]:
        return list(self._results)
