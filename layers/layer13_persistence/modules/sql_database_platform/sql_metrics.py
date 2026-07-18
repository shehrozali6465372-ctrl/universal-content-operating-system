"""sql_metrics.py — SQL platform metrics."""
from __future__ import annotations
import time
from typing import Any, Dict


class SQLMetrics:
    """Tracks SQL platform metrics."""

    def __init__(self) -> None:
        self._queries: int = 0
        self._errors: int = 0
        self._total_time_ms: float = 0.0
        self._by_type: Dict[str, int] = {}
        self._start_time: float = time.time()

    def record_query(self, query_type: str, execution_ms: float, success: bool = True) -> None:
        self._queries += 1
        self._total_time_ms += execution_ms
        self._by_type[query_type] = self._by_type.get(query_type, 0) + 1
        if not success:
            self._errors += 1

    def get_avg_time(self) -> float:
        return self._total_time_ms / max(1, self._queries)

    def get_error_rate(self) -> float:
        return self._errors / max(1, self._queries)

    def get_queries_per_second(self) -> float:
        elapsed = time.time() - self._start_time
        return self._queries / max(1.0, elapsed)

    def reset(self) -> None:
        self._queries = 0
        self._errors = 0
        self._total_time_ms = 0.0
        self._by_type.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"queries": self._queries, "errors": self._errors,
                "avg_time_ms": self.get_avg_time(),
                "error_rate": self.get_error_rate(),
                "by_type": dict(self._by_type)}
