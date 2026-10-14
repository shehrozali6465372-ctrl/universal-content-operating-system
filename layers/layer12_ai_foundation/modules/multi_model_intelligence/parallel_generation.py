"""ParallelGeneration — bounded concurrent provider-backed generation."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .models import ModelResponse
from .parallel_utils import execute_parallel_calls


class ParallelGeneration:
    """Generate content concurrently; never synthesize a model response."""

    def __init__(self, max_parallel: int = 5) -> None:
        if max_parallel < 1:
            raise ValueError("max_parallel must be positive")
        self.max_parallel = max_parallel
        self._history: List[Dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        models: List[str],
        call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
        **kwargs: Any,
    ) -> List[ModelResponse]:
        targets = models[: self.max_parallel]
        start = time.monotonic()
        results = execute_parallel_calls(
            prompt, targets, call_fn, max_workers=self.max_parallel
        )
        elapsed = (time.monotonic() - start) * 1000
        self._history.append(
            {
                "prompt": prompt[:100],
                "models_used": len(results),
                "elapsed_ms": elapsed,
            }
        )
        return results

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
