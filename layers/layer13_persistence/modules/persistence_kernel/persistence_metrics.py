"""persistence_metrics.py — Persistence metrics tracking."""
from __future__ import annotations
import time
from typing import Any, Dict


class PersistenceMetrics:
    """Tracks persistence system metrics."""

    __slots__ = ("_records", "_stores_registered", "_total_operations",
                 "_total_errors", "_by_type", "_start_time")

    def __init__(self) -> None:
        self._records: Dict[str, int] = {}
        self._stores_registered: int = 0
        self._total_operations: int = 0
        self._total_errors: int = 0
        self._by_type: Dict[str, int] = {}
        self._start_time = time.time()

    def record_store_registered(self, name: str) -> None:
        self._stores_registered += 1

    def record_operation(self, op_type: str, success: bool = True) -> None:
        self._total_operations += 1
        self._by_type[op_type] = self._by_type.get(op_type, 0) + 1
        if not success:
            self._total_errors += 1

    def record_count(self, store: str, count: int) -> None:
        self._records[store] = count

    def get_total(self) -> int:
        return sum(self._records.values())

    def get_error_rate(self) -> float:
        if self._total_operations == 0:
            return 0.0
        return self._total_errors / self._total_operations

    def to_dict(self) -> Dict[str, Any]:
        return {"stores_registered": self._stores_registered,
                "total_operations": self._total_operations,
                "total_errors": self._total_errors,
                "error_rate": self.get_error_rate(),
                "by_type": dict(self._by_type),
                "records": dict(self._records)}
