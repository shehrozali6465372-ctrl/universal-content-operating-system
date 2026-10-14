"""ParallelReview — concurrent review via real provider-backed critics."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .models import ModelResponse
from .parallel_utils import execute_parallel_calls


class ParallelReview:
    """Review content concurrently; never fabricate a positive review."""

    def __init__(self, max_concurrent: int = 5) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be positive")
        self.max_concurrent = max_concurrent
        self._history: List[Dict[str, Any]] = []

    def review(
        self,
        content: str,
        reviewers: List[str],
        call_fn: Optional[Callable[[str, str], ModelResponse]] = None,
        **kwargs: Any,
    ) -> List[ModelResponse]:
        targets = reviewers[: self.max_concurrent]
        start = time.monotonic()
        results = execute_parallel_calls(
            content, targets, call_fn, max_workers=self.max_concurrent
        )
        elapsed = (time.monotonic() - start) * 1000
        self._history.append(
            {
                "content_len": len(content),
                "reviewers": len(results),
                "elapsed_ms": elapsed,
            }
        )
        return results

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
