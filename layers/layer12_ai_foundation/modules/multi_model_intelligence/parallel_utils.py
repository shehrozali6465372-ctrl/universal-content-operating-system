"""Shared bounded concurrent execution for model-backed operations."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Sequence

from .models import ModelResponse


def execute_parallel_calls(
    prompt: str,
    targets: Sequence[str],
    call_fn: Callable[[str, str], ModelResponse] | None,
    max_workers: int,
) -> list[ModelResponse]:
    """Execute real callbacks concurrently and preserve caller-specified result order."""
    if not callable(call_fn):
        raise ValueError("call_fn must be a real provider callback; synthetic results are disabled")
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    if not targets:
        return []

    results: list[ModelResponse | None] = [None] * len(targets)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as pool:
        future_targets = {
            pool.submit(call_fn, prompt, target): (index, target)
            for index, target in enumerate(targets)
        }
        for future in as_completed(future_targets):
            index, target = future_targets[future]
            try:
                response = future.result()
                if not isinstance(response, ModelResponse):
                    raise TypeError("provider callback must return ModelResponse")
                results[index] = response
            except Exception as exc:
                results[index] = ModelResponse(
                    model=target,
                    provider="error",
                    content="",
                    error=str(exc) or type(exc).__name__,
                    confidence=0.0,
                )

    return [result for result in results if result is not None]
