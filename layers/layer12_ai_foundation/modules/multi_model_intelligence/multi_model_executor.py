"""MultiModelExecutor — bounded multi-model execution with explicit failures."""
from __future__ import annotations

import time
from typing import Any, Callable, List, Optional

from .models import ModelResponse


class MultiModelExecutor:
    """Execute provider-backed model calls; never synthesize a model response."""

    def __init__(self, max_retries: int = 2, timeout: float = 30.0) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.max_retries = max_retries
        self.timeout = timeout
        self._execution_count = 0

    def execute(
        self,
        prompt: str,
        models: List[str],
        call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
        **kwargs: Any,
    ) -> List[ModelResponse]:
        """Call a real adapter for each model and return explicit success/failure results.

        The timeout is an overall execution deadline. A synchronous provider call
        cannot be forcibly cancelled by this helper, but a result arriving after
        the deadline is never reported as a successful, on-time completion.
        """
        if not models:
            self._execution_count += 1
            return []
        if not callable(call_fn):
            raise ValueError(
                "call_fn must be a real provider callback; synthetic model responses are disabled"
            )

        results: List[ModelResponse] = []
        deadline = time.monotonic() + self.timeout

        for model in models:
            success = False
            last_error = "provider returned an unsuccessful response"

            for attempt in range(self.max_retries + 1):
                if time.monotonic() >= deadline:
                    results.append(
                        ModelResponse(model=model, provider="timeout", content="", error="Timeout")
                    )
                    break

                try:
                    response = call_fn(prompt, model)
                    if not isinstance(response, ModelResponse):
                        raise TypeError("provider callback must return ModelResponse")

                    if time.monotonic() >= deadline:
                        results.append(
                            ModelResponse(model=model, provider="timeout", content="", error="Timeout")
                        )
                        break

                    if response.is_success:
                        results.append(response)
                        success = True
                        break

                    last_error = response.error or "provider returned an unsuccessful response"
                except Exception as exc:
                    last_error = str(exc) or type(exc).__name__

                if time.monotonic() >= deadline:
                    results.append(
                        ModelResponse(model=model, provider="timeout", content="", error="Timeout")
                    )
                    break
                if attempt == self.max_retries:
                    results.append(
                        ModelResponse(model=model, provider="error", content="", error=last_error)
                    )

            if not success and not any(r.model == model for r in results):
                results.append(
                    ModelResponse(model=model, provider="error", content="", error=last_error)
                )

        self._execution_count += 1
        return results

    @property
    def execution_count(self) -> int:
        return self._execution_count
