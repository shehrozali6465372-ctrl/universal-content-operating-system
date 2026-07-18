"""MultiModelPolicy — policies for multi-model operations."""
from __future__ import annotations

from typing import Any, Dict, List


class MultiModelPolicy:
    """Policy engine for multi-model intelligence operations."""

    DEFAULT_POLICIES = {
        "min_models_for_consensus": 2,
        "max_cost_per_request": 0.10,
        "max_latency_ms": 10000,
        "min_confidence_for_accept": 0.5,
        "require_diverse_providers": True,
        "fallback_to_single_model": True,
        "enable_cost_optimization": True,
        "cache_results": True,
    }

    def __init__(self, **kwargs: Any) -> None:
        self.policies = dict(self.DEFAULT_POLICIES)
        self.policies.update(kwargs)

    def get(self, key: str, default: Any = None) -> Any:
        return self.policies.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.policies[key] = value

    def check(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        violations: List[str] = []

        if operation == "consensus":
            models_used = params.get("models_used", 0)
            if models_used < self.policies["min_models_for_consensus"]:
                violations.append(f"Need {self.policies['min_models_for_consensus']} models")

        if operation == "cost":
            cost = params.get("cost", 0.0)
            if cost > self.policies["max_cost_per_request"]:
                violations.append(f"Cost ${cost:.4f} exceeds budget ${self.policies['max_cost_per_request']:.4f}")

        if operation == "latency":
            latency = params.get("latency_ms", 0)
            if latency > self.policies["max_latency_ms"]:
                violations.append(f"Latency {latency}ms exceeds limit")

        return {"allowed": len(violations) == 0, "violations": violations}

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.policies)
