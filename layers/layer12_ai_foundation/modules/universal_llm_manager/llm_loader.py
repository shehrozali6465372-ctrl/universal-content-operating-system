"""LLMLoader — Dynamic model loading."""
from __future__ import annotations
from typing import Any, Dict, List

class LLMLoader:
    def __init__(self) -> None:
        self._loaded: Dict[str, Dict[str, Any]] = {}
    def load(self, provider: str, model: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        key = f"{provider}:{model}"
        entry = {"provider": provider, "model": model, "config": config or {}, "loaded": True}
        self._loaded[key] = entry
        return entry
    def unload(self, provider: str, model: str) -> bool:
        key = f"{provider}:{model}"
        return self._loaded.pop(key, None) is not None
    def is_loaded(self, provider: str, model: str) -> bool:
        return f"{provider}:{model}" in self._loaded
    def get_loaded(self) -> List[Dict[str, Any]]:
        return list(self._loaded.values())
    def get_stats(self) -> Dict[str, Any]:
        return {"loaded_models": len(self._loaded)}
