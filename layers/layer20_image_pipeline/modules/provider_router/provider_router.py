"""ProviderRouter — route image generation to multiple providers."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class ProviderStatus(str, Enum):
    AVAILABLE = "available"; BUSY = "busy"; ERROR = "error"; DISABLED = "disabled"


class ImageProvider:
    __slots__ = ("name", "status", "cost_per_image", "quality_score",
                 "speed_score", "handler", "metadata")

    def __init__(self, name: str, handler: Optional[Callable] = None,
                 cost_per_image: float = 0.0) -> None:
        self.name = name
        self.status = ProviderStatus.AVAILABLE
        self.cost_per_image = cost_per_image
        self.quality_score = 0.8
        self.speed_score = 0.8
        self.handler = handler
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "status": self.status.value,
                "cost": self.cost_per_image, "quality": self.quality_score}


class ProviderRouter:
    def __init__(self) -> None:
        self._providers: Dict[str, ImageProvider] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, name: str, handler: Optional[Callable] = None,
                 cost_per_image: float = 0.0) -> ImageProvider:
        provider = ImageProvider(name, handler, cost_per_image)
        self._providers[name] = provider
        return provider

    def unregister(self, name: str) -> bool:
        if name in self._providers:
            del self._providers[name]
            return True
        return False

    def route(self, prompt: Dict[str, Any], strategy: str = "cheapest") -> Optional[Dict[str, Any]]:
        available = [p for p in self._providers.values() if p.status == ProviderStatus.AVAILABLE]
        if not available:
            return None
        if strategy == "cheapest":
            provider = min(available, key=lambda p: p.cost_per_image)
        elif strategy == "highest_quality":
            provider = max(available, key=lambda p: p.quality_score)
        elif strategy == "fastest":
            provider = max(available, key=lambda p: p.speed_score)
        else:
            provider = available[0]
        self._history.append({"provider": provider.name, "strategy": strategy, "time": time.time()})
        if provider.handler:
            try:
                return {"provider": provider.name, "result": provider.handler(prompt)}
            except Exception as exc:
                return {"provider": provider.name, "error": str(exc)}
        return {"provider": provider.name, "status": "no_handler"}

    def list_providers(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._providers.values()]

    def get_provider(self, name: str) -> Optional[ImageProvider]:
        return self._providers.get(name)

    def set_status(self, name: str, status: ProviderStatus) -> bool:
        provider = self._providers.get(name)
        if provider:
            provider.status = status
            return True
        return False
