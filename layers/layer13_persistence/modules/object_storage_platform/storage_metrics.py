"""storage_metrics.py — Storage metrics."""
from __future__ import annotations
from typing import Any, Dict


class StorageMetrics:
    """Tracks storage metrics."""

    def __init__(self) -> None:
        self._total_objects: int = 0
        self._total_bytes: int = 0
        self._total_operations: int = 0
        self._errors: int = 0
        self._by_type: Dict[str, int] = {}

    def record_object(self, size_bytes: int) -> None:
        self._total_objects += 1
        self._total_bytes += size_bytes

    def record_operation(self, op_type: str, success: bool = True) -> None:
        self._total_operations += 1
        self._by_type[op_type] = self._by_type.get(op_type, 0) + 1
        if not success:
            self._errors += 1

    def get_error_rate(self) -> float:
        return self._errors / max(1, self._total_operations)

    def reset(self) -> None:
        self._total_objects = 0
        self._total_bytes = 0
        self._total_operations = 0
        self._errors = 0
        self._by_type.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"objects": self._total_objects, "bytes": self._total_bytes,
                "operations": self._total_operations, "errors": self._errors,
                "error_rate": self.get_error_rate()}
