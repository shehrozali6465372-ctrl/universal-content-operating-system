"""Strategy Validator — Validate strategies before deployment."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile


class StrategyValidationError:
    """A validation error found in a strategy."""

    __slots__ = ("field", "severity", "message", "suggestion")

    def __init__(self, field: str = "", severity: str = "error", message: str = "") -> None:
        self.field = field
        self.severity = severity
        self.message = message
        self.suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
        }


class StrategyValidationResult:
    """Result of validating a strategy."""

    __slots__ = ("strategy_id", "is_valid", "errors", "warnings", "score")

    def __init__(self, strategy_id: str = "") -> None:
        self.strategy_id = strategy_id
        self.is_valid: bool = True
        self.errors: List[StrategyValidationError] = []
        self.warnings: List[StrategyValidationError] = []
        self.score: float = 100.0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "score": round(self.score, 2),
        }


class StrategyValidator:
    """Validate strategy profiles for deployment readiness."""

    def __init__(self) -> None:
        self._results: List[StrategyValidationResult] = []

    def validate(self, strategy: StrategyProfile) -> StrategyValidationResult:
        result = StrategyValidationResult(strategy.strategy_id)
        errors = []
        warnings = []
        errors.extend(self._validate_name(strategy))
        errors.extend(self._validate_type(strategy))
        warnings.extend(self._validate_targeting(strategy))
        warnings.extend(self._validate_content(strategy))
        warnings.extend(self._validate_performance(strategy))
        result.errors = [e for e in errors if e.severity == "error"]
        result.warnings = warnings
        result.is_valid = len(result.errors) == 0
        result.score = self._compute_score(result)
        self._results.append(result)
        return result

    def validate_batch(self, strategies: List[StrategyProfile]) -> List[StrategyValidationResult]:
        return [self.validate(s) for s in strategies]

    def _validate_name(self, s: StrategyProfile) -> List[StrategyValidationError]:
        errors = []
        if not s.name:
            e = StrategyValidationError("name", "error", "Strategy name is empty")
            e.suggestion = "Provide a descriptive strategy name"
            errors.append(e)
        return errors

    def _validate_type(self, s: StrategyProfile) -> List[StrategyValidationError]:
        errors = []
        valid = ("engagement", "growth", "conversion", "brand_awareness",
                 "education", "entertainment", "community", "thought_leadership")
        if s.strategy_type not in valid:
            errors.append(StrategyValidationError("strategy_type", "error", f"Invalid type: {s.strategy_type}"))
        return errors

    def _validate_targeting(self, s: StrategyProfile) -> List[StrategyValidationError]:
        warnings = []
        if not s.target_platforms:
            warnings.append(StrategyValidationError("target_platforms", "warning", "No target platforms"))
        if not s.target_audience:
            warnings.append(StrategyValidationError("target_audience", "warning", "No target audience"))
        return warnings

    def _validate_content(self, s: StrategyProfile) -> List[StrategyValidationError]:
        warnings = []
        if not s.content_pillars:
            warnings.append(StrategyValidationError("content_pillars", "warning", "No content pillars"))
        if not s.tone_guidelines:
            warnings.append(StrategyValidationError("tone_guidelines", "warning", "No tone guidelines"))
        return warnings

    def _validate_performance(self, s: StrategyProfile) -> List[StrategyValidationError]:
        warnings = []
        if s.usage_count > 0 and s.avg_engagement < 0.1:
            warnings.append(StrategyValidationError(
                "performance", "warning", f"Very low engagement: {s.avg_engagement}",
            ))
        return warnings

    def _compute_score(self, result: StrategyValidationResult) -> float:
        score = 100.0
        score -= len(result.errors) * 20.0
        score -= len(result.warnings) * 5.0
        return max(0.0, min(100.0, score))

    def get_results(self) -> List[StrategyValidationResult]:
        return list(self._results)

    def get_invalid_count(self) -> int:
        return sum(1 for r in self._results if not r.is_valid)
