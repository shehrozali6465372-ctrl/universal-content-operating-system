"""LLMRegistry — Register available models and providers."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class ModelInfo:
    __slots__ = ("provider", "model", "version", "max_tokens", "pricing", "capabilities", "registered_at")
    def __init__(self, provider: str = "", model: str = "") -> None:
        self.provider = provider; self.model = model; self.version = "1.0.0"
        self.max_tokens: int = 128000; self.pricing: Dict[str, float] = {}
        self.capabilities: List[str] = []; self.registered_at = time.time()
    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "model": self.model, "max_tokens": self.max_tokens}

class LLMRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, ModelInfo] = {}
    def register(self, provider: str, model: str, **kwargs) -> ModelInfo:
        key = f"{provider}:{model}"
        if key in self._models:
            return self._models[key]
        info = ModelInfo(provider, model)
        for k, v in kwargs.items():
            if hasattr(info, k):
                setattr(info, k, v)
        self._models[key] = info
        return info
    def get(self, provider: str, model: str) -> ModelInfo:
        return self._models.get(f"{provider}:{model}")
    def get_by_provider(self, provider: str) -> List[ModelInfo]:
        return [m for m in self._models.values() if m.provider == provider]
    def get_all(self) -> List[ModelInfo]:
        return list(self._models.values())
    def get_stats(self) -> Dict[str, Any]:
        providers: Dict[str, int] = {}
        for m in self._models.values():
            providers[m.provider] = providers.get(m.provider, 0) + 1
        return {"total": len(self._models), "by_provider": providers}
