"""Production-safe multi-provider image routing."""
from __future__ import annotations

from enum import Enum
import threading
import time
from typing import Any, Callable, Dict, List, Optional


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class ImageProvider:
    __slots__ = (
        "name",
        "status",
        "cost_per_image",
        "quality_score",
        "speed_score",
        "handler",
        "metadata",
    )

    def __init__(
        self,
        name: str,
        handler: Optional[Callable] = None,
        cost_per_image: float = 0.0,
    ) -> None:
        if not name or not name.strip():
            raise ValueError("provider name is required")
        if cost_per_image < 0:
            raise ValueError("cost_per_image cannot be negative")
        self.name = name
        self.status = ProviderStatus.AVAILABLE
        self.cost_per_image = cost_per_image
        self.quality_score: Optional[float] = None
        self.speed_score: Optional[float] = None
        self.handler = handler
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "cost": self.cost_per_image,
            "quality": self.quality_score,
            "speed": self.speed_score,
        }


class ProviderRouter:
    def __init__(self) -> None:
        self._providers: Dict[str, ImageProvider] = {}
        self._history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def register(
        self,
        name: str,
        handler: Optional[Callable] = None,
        cost_per_image: float = 0.0,
    ) -> ImageProvider:
        provider = ImageProvider(name, handler, cost_per_image)
        with self._lock:
            self._providers[name] = provider
        return provider

    def unregister(self, name: str) -> bool:
        with self._lock:
            return self._providers.pop(name, None) is not None

    def route(
        self, prompt: Dict[str, Any], strategy: str = "cheapest"
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(prompt, dict):
            raise TypeError("prompt must be a dictionary")
        if not strategy or not strategy.strip():
            raise ValueError("strategy is required")

        with self._lock:
            available = [
                provider
                for provider in self._providers.values()
                if provider.status == ProviderStatus.AVAILABLE
            ]
            if not available:
                return {"error": "no_available_provider"}

            if strategy == "cheapest":
                provider = min(available, key=lambda item: item.cost_per_image)
            elif strategy == "highest_quality":
                measured = [
                    item for item in available if item.quality_score is not None
                ]
                if not measured:
                    return {"error": "no_provider_quality_telemetry"}
                provider = max(measured, key=lambda item: item.quality_score)
            elif strategy == "fastest":
                measured = [
                    item for item in available if item.speed_score is not None
                ]
                if not measured:
                    return {"error": "no_provider_speed_telemetry"}
                provider = max(measured, key=lambda item: item.speed_score)
            else:
                raise ValueError(f"unsupported routing strategy: {strategy}")

            if provider.handler is None:
                return {
                    "provider": provider.name,
                    "error": "provider_handler_not_configured",
                }

            self._history.append(
                {
                    "provider": provider.name,
                    "strategy": strategy,
                    "time": time.time(),
                }
            )
            handler = provider.handler

        started = time.perf_counter()
        try:
            value = handler(prompt)
        except Exception as exc:
            with self._lock:
                provider.metadata["last_error_type"] = type(exc).__name__
                provider.metadata["last_error"] = str(exc)
            return {
                "provider": provider.name,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }

        elapsed = time.perf_counter() - started
        with self._lock:
            provider.metadata["last_latency_seconds"] = elapsed
        return {
            "provider": provider.name,
            "result": value,
            "latency_seconds": elapsed,
        }

    def record_observation(
        self,
        name: str,
        quality_score: Optional[float] = None,
        speed_score: Optional[float] = None,
    ) -> bool:
        with self._lock:
            provider = self._providers.get(name)
            if provider is None:
                return False
            for label, value in (
                ("quality", quality_score),
                ("speed", speed_score),
            ):
                if value is not None and not 0.0 <= value <= 1.0:
                    raise ValueError(f"{label}_score must be between 0 and 1")
            if quality_score is not None:
                provider.quality_score = quality_score
            if speed_score is not None:
                provider.speed_score = speed_score
            return True

    def list_providers(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [provider.to_dict() for provider in self._providers.values()]

    def get_provider(self, name: str) -> Optional[ImageProvider]:
        with self._lock:
            return self._providers.get(name)

    def set_status(self, name: str, status: ProviderStatus) -> bool:
        if not isinstance(status, ProviderStatus):
            raise TypeError("status must be ProviderStatus")
        with self._lock:
            provider = self._providers.get(name)
            if provider is None:
                return False
            provider.status = status
            return True

    def history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._history]
