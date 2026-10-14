"""ParallelReasoning — bounded concurrent provider-backed reasoning."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .models import ModelResponse
from .parallel_utils import execute_parallel_calls


class ParallelReasoning:
    """Reason across models concurrently using an injected real provider callback."""

    def __init__(self, max_concurrent: int = 5) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be positive")
        self.max_concurrent = max_concurrent
        self._history: List[Dict[str, Any]] = []

    def reason(
        self,
        prompt: str,
        models: List[str],
        call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
        **kwargs: Any,
    ) -> List[ModelResponse]:
        targets = models[: self.max_concurrent]
        start = time.monotonic()
        results = execute_parallel_calls(
            prompt, targets, call_fn, max_workers=self.max_concurrent
        )
        elapsed = (time.monotonic() - start) * 1000
        self._history.append(
            {
                "prompt": prompt[:100],
                "models": list(targets),
                "elapsed_ms": elapsed,
                "results": len(results),
            }
        )
        return results

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
