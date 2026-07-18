"""MultiModelValidator — validate inputs and outputs of multi-model operations."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ModelResponse


class MultiModelValidator:
    """Validate inputs and outputs for multi-model intelligence."""

    def __init__(self, min_models: int = 2, max_models: int = 10,
                 min_confidence: float = 0.0) -> None:
        self.min_models = min_models
        self.max_models = max_models
        self.min_confidence = min_confidence

    def validate_request(self, prompt: str, models: List[str]) -> Dict[str, Any]:
        errors: List[str] = []
        if not prompt or not prompt.strip():
            errors.append("Empty prompt")
        if len(models) < self.min_models:
            errors.append(f"Need at least {self.min_models} models, got {len(models)}")
        if len(models) > self.max_models:
            errors.append(f"Too many models: {len(models)} > {self.max_models}")
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_responses(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        if not responses:
            return {"valid": False, "errors": ["No responses"]}
        successful = [r for r in responses if r.is_success]
        return {
            "valid": len(successful) >= 1,
            "total": len(responses),
            "successful": len(successful),
            "failed": len(responses) - len(successful),
        }

    def validate_consensus(self, consensus_score: float,
                           threshold: float = 0.5) -> bool:
        return consensus_score >= threshold

    def validate_confidence(self, confidence: float) -> bool:
        return confidence >= self.min_confidence
