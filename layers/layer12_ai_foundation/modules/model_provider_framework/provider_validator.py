"""provider_validator.py — Provider validation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderRequest


class ProviderValidator:
    """Validates provider requests and configurations."""

    def validate_request(self, request: ProviderRequest) -> List[str]:
        errors: List[str] = []
        if not request.prompt and not request.messages:
            errors.append("Either prompt or messages required")
        if request.temperature < 0 or request.temperature > 2.0:
            errors.append("Temperature must be 0.0-2.0")
        if request.max_tokens < 1:
            errors.append("max_tokens must be >= 1")
        if request.max_tokens > 128000:
            errors.append("max_tokens exceeds maximum")
        return errors

    def is_valid_request(self, request: ProviderRequest) -> bool:
        return len(self.validate_request(request)) == 0

    def validate_config(self, config: Dict[str, Any],
                        required: Optional[List[str]] = None) -> List[str]:
        errors: List[str] = []
        req_keys = required or ["api_key"]
        for key in req_keys:
            if key not in config or not config[key]:
                errors.append(f"Missing required config: {key}")
        return errors

    def validate_model(self, model: str, supported: List[str]) -> bool:
        if not supported:
            return True
        return model in supported
