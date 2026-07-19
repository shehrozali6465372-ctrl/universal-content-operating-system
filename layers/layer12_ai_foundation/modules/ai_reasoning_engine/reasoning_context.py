"""ReasoningContext — context management for reasoning operations."""
from __future__ import annotations

from typing import Any, Dict, List


class ReasoningContext:
    """Context for tracking state during reasoning."""

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {}
        self._steps_log: List[str] = []

    def set(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def log_step(self, description: str) -> None:
        self._steps_log.append(description)

    def get_steps(self) -> List[str]:
        return list(self._steps_log)

    def clear(self) -> None:
        self._context.clear()
        self._steps_log.clear()
