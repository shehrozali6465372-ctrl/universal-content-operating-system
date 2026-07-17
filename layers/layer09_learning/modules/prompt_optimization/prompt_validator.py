"""Prompt Validator — Validate prompts before deployment."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile


class ValidationError:
    """A validation error found in a prompt."""

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


class ValidationResult:
    """Result of validating a prompt."""

    __slots__ = ("profile_id", "is_valid", "errors", "warnings", "score")

    def __init__(self, profile_id: str = "") -> None:
        self.profile_id = profile_id
        self.is_valid: bool = True
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.score: float = 100.0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "score": round(self.score, 2),
        }


class PromptValidator:
    """Validate prompt profiles for deployment readiness."""

    MIN_TEMPLATE_LENGTH = 10
    MAX_TEMPLATE_LENGTH = 10000
    MIN_CONFIDENCE = 0.3

    def __init__(self) -> None:
        self._results: List[ValidationResult] = []

    def validate(self, profile: PromptProfile) -> ValidationResult:
        result = ValidationResult(profile.profile_id)
        errors = []
        warnings = []
        errors.extend(self._validate_template(profile))
        errors.extend(self._validate_category(profile))
        warnings.extend(self._validate_metadata(profile))
        warnings.extend(self._validate_performance(profile))
        result.errors = [e for e in errors if e.severity == "error"]
        result.warnings = warnings
        result.is_valid = len(result.errors) == 0
        result.score = self._compute_score(result)
        self._results.append(result)
        return result

    def validate_batch(self, profiles: List[PromptProfile]) -> List[ValidationResult]:
        return [self.validate(p) for p in profiles]

    def _validate_template(self, p: PromptProfile) -> List[ValidationError]:
        errors = []
        if not p.template:
            e = ValidationError("template", "error", "Template is empty")
            e.suggestion = "Provide a non-empty prompt template"
            errors.append(e)
        elif len(p.template) < self.MIN_TEMPLATE_LENGTH:
            e = ValidationError("template", "error", f"Template too short ({len(p.template)} chars, min {self.MIN_TEMPLATE_LENGTH})")
            e.suggestion = "Expand the template with more detailed instructions"
            errors.append(e)
        if len(p.template) > self.MAX_TEMPLATE_LENGTH:
            e = ValidationError("template", "error", f"Template too long ({len(p.template)} chars, max {self.MAX_TEMPLATE_LENGTH})")
            errors.append(e)
        return errors

    def _validate_category(self, p: PromptProfile) -> List[ValidationError]:
        errors = []
        valid = ("content_generation", "caption", "hook", "cta",
                 "hashtag", "seo", "tone", "brand", "strategy")
        if p.category not in valid:
            errors.append(ValidationError("category", "error", f"Invalid category: {p.category}"))
        return errors

    def _validate_metadata(self, p: PromptProfile) -> List[ValidationError]:
        warnings = []
        if not p.platform:
            warnings.append(ValidationError("platform", "warning", "No target platform specified"))
        if not p.tone:
            warnings.append(ValidationError("tone", "warning", "No tone specified"))
        if not p.tags:
            warnings.append(ValidationError("tags", "warning", "No tags specified"))
        return warnings

    def _validate_performance(self, p: PromptProfile) -> List[ValidationError]:
        warnings = []
        if p.usage_count > 0 and p.avg_quality_score < self.MIN_CONFIDENCE:
            warnings.append(ValidationError(
                "performance", "warning",
                f"Low quality score: {p.avg_quality_score}",
            ))
        return warnings

    def _compute_score(self, result: ValidationResult) -> float:
        score = 100.0
        score -= len(result.errors) * 20.0
        score -= len(result.warnings) * 5.0
        return max(0.0, min(100.0, score))

    def get_results(self) -> List[ValidationResult]:
        return list(self._results)

    def get_invalid_count(self) -> int:
        return sum(1 for r in self._results if not r.is_valid)
