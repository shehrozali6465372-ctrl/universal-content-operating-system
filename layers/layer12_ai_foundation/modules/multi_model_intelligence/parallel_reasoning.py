"""ParallelReasoning — reason across multiple models in parallel."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .models import ModelResponse


class ParallelReasoning:
    """Execute reasoning across multiple models concurrently (simulated)."""

    def __init__(self, max_concurrent: int = 5) -> None:
        self.max_concurrent = max_concurrent
        self._history: List[Dict[str, Any]] = []

    def reason(self, prompt: str, models: List[str],
               call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
               **kwargs: Any) -> List[ModelResponse]:
        results: List[ModelResponse] = []
        start = time.time()

        for model in models:
            if call_fn:
                try:
                    r = call_fn(prompt, model)
                    results.append(r)
                except Exception as exc:
                    results.append(ModelResponse(model=model, provider="unknown",
                                                 content="", error=str(exc)))
            else:
                # Simulated response
                results.append(ModelResponse(
                    model=model, provider="simulated",
                    content=f"Reasoning from {model} for: {prompt[:80]}",
                    confidence=0.7, latency_ms=100.0 + len(results) * 50,
                ))

        elapsed = (time.time() - start) * 1000
        self._history.append({"prompt": prompt[:100], "models": models,
                              "elapsed_ms": elapsed, "results": len(results)})
        return results

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
