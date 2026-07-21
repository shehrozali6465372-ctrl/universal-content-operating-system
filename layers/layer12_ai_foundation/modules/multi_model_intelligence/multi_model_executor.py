"""MultiModelExecutor — execute multi-model operations."""
from __future__ import annotations

import time
from typing import Any, Callable, List, Optional

from .models import ModelResponse


class MultiModelExecutor:
    """Execute multi-model operations with retry and fallback."""

    def __init__(self, max_retries: int = 2, timeout: float = 30.0) -> None:
        self.max_retries = max_retries
        self.timeout = timeout
        self._execution_count = 0

    def execute(self, prompt: str, models: List[str],
                call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
                **kwargs: Any) -> List[ModelResponse]:
        results: List[ModelResponse] = []
        start = time.time()

        for model in models:
            success = False
            for attempt in range(self.max_retries + 1):
                elapsed = (time.time() - start) * 1000
                if elapsed > self.timeout * 1000:
                    results.append(ModelResponse(model=model, provider="timeout",
                                                 content="", error="Timeout"))
                    break

                try:
                    if call_fn:
                        response = call_fn(prompt, model)
                    else:
                        response = ModelResponse(
                            model=model, provider="error",
                            content=f"Response from {model}",
                            confidence=0.75, latency_ms=100.0,
                        )
                    if response.is_success:
                        results.append(response)
                        success = True
                        break
                except Exception as exc:
                    if attempt == self.max_retries:
                        results.append(ModelResponse(model=model, provider="error",
                                                     content="", error=str(exc)))
            if not success and not any(r.model == model for r in results):
                results.append(ModelResponse(model=model, provider="unknown",
                                             content="", error="Max retries exceeded"))

        self._execution_count += 1
        return results

    @property
    def execution_count(self) -> int:
        return self._execution_count
