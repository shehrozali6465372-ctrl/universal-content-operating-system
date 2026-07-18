"""PromptContext — context management for prompt generation."""
from __future__ import annotations

from typing import Any, Dict, List


class PromptContext:
    """Context manager for tracking state during prompt generation."""

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {}
        self._stack: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def push(self) -> None:
        self._stack.append(dict(self._context))

    def pop(self) -> None:
        if self._stack:
            self._context = self._stack.pop()

    def merge(self, context: Dict[str, Any]) -> None:
        self._context.update(context)

    def keys(self) -> List[str]:
        return list(self._context.keys())

    def clear(self) -> None:
        self._context.clear()
        self._stack.clear()
