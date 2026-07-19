"""OrchestratorConfig — configuration for AI orchestrator."""
from __future__ import annotations
from typing import Any, Dict, List

class OrchestratorConfig:
    def __init__(self, **kwargs: Any) -> None:
        self.max_concurrent: int = kwargs.get("max_concurrent", 5)
        self.timeout_seconds: float = kwargs.get("timeout_seconds", 30.0)
        self.max_retries: int = kwargs.get("max_retries", 3)
        self.enable_retry: bool = kwargs.get("enable_retry", True)
        self.enable_caching: bool = kwargs.get("enable_caching", True)
        self.enable_monitoring: bool = kwargs.get("enable_monitoring", True)
        self.default_model: str = kwargs.get("default_model", "gpt-4o-mini")
        self.fallback_model: str = kwargs.get("fallback_model", "gemini-2.0-flash")
        self.layers_enabled: List[str] = kwargs.get("layers_enabled",
            ["llm_manager", "multi_model", "prompt", "memory", "reasoning", "cost", "evaluation", "governance"])
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
