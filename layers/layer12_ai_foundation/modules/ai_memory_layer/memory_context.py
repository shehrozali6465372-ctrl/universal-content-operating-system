"""MemoryContext — context management for memory operations."""
from __future__ import annotations

from typing import Any, Dict, List


class MemoryContext:
    """Context for tracking state during memory operations."""

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {}
        self._operations: List[str] = []

    def set(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def record_operation(self, operation: str) -> None:
        self._operations.append(operation)

    def get_operations(self) -> List[str]:
        return list(self._operations)

    def clear(self) -> None:
        self._context.clear()
        self._operations.clear()
