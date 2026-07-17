"""Calibration Validator — Validate calibration quality and consistency."""
from __future__ import annotations
from typing import Any, Dict, List


class CalibrationValidationResult:
    """Result of validating calibration."""

    __slots__ = ("is_valid", "checks", "warnings", "score")

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.checks: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
        self.score: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "check_count": len(self.checks),
            "warning_count": len(self.warnings),
            "score": round(self.score, 2),
        }


class CalibrationValidator:
    """Validate calibration quality and consistency."""

    def __init__(self) -> None:
        self._results: List[CalibrationValidationResult] = []

    def validate(self, biases: Dict[str, float],
                 sample_counts: Dict[str, int] = None,
                 ece: float = 0.0) -> CalibrationValidationResult:
        result = CalibrationValidationResult()
        sample_counts = sample_counts or {}

        for metric, bias in biases.items():
            check = {"metric": metric, "bias": bias, "status": "pass"}
            if abs(bias) > 0.3:
                check["status"] = "warning"
                result.warnings.append(f"High bias for {metric}: {bias:.4f}")
            if abs(bias) > 0.5:
                check["status"] = "fail"
                result.is_valid = False
            samples = sample_counts.get(metric, 0)
            if samples < 10:
                check["status"] = "warning"
                result.warnings.append(f"Low sample count for {metric}: {samples}")
            result.checks.append(check)

        if ece > 0.2:
            result.is_valid = False
            result.warnings.append(f"High ECE: {ece:.4f}")

        result.score = self._compute_score(result)
        self._results.append(result)
        return result

    def _compute_score(self, result: CalibrationValidationResult) -> float:
        score = 100.0
        for check in result.checks:
            if check["status"] == "fail":
                score -= 20
            elif check["status"] == "warning":
                score -= 5
        score -= len(result.warnings) * 3
        return max(0.0, min(100.0, score))

    def get_results(self) -> List[CalibrationValidationResult]:
        return list(self._results)
