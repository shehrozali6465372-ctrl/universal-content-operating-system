"""MultiModelFallback — fallback strategies when primary models fail."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .models import ModelResponse


class MultiModelFallback:
    """Fallback strategies when primary multi-model operations fail."""

    def __init__(self, fallback_models: Optional[List[str]] = None) -> None:
        self.fallback_models = fallback_models or ["gpt-4o-mini", "deepseek-chat"]
        self._fallback_history: List[Dict[str, Any]] = []

    def attempt_fallback(self, prompt: str, failed_models: List[str],
                         call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
                         **kwargs: Any) -> Optional[ModelResponse]:
        available = [m for m in self.fallback_models if m not in failed_models]
        if not available:
            return None

        for model in available:
            try:
                if call_fn:
                    response = call_fn(prompt, model)
                    if response.is_success:
                        self._fallback_history.append({"model": model, "success": True})
                        return response
                else:
                    response = ModelResponse(
                        model=model, provider="fallback",
                        content=f"Fallback response from {model}",
                        confidence=0.6, latency_ms=200.0,
                    )
                    self._fallback_history.append({"model": model, "success": True})
                    return response
            except Exception as exc:
                self._fallback_history.append({"model": model, "success": False,
                                               "error": str(exc)})

        return None

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._fallback_history)
