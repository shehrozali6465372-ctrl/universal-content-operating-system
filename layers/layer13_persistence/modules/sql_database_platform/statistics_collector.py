"""statistics_collector.py — Database statistics collection."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class StatisticsCollector:
    """Collects database statistics."""

    def __init__(self) -> None:
        self._table_stats: Dict[str, Dict[str, Any]] = {}
        self._query_stats: List[Dict[str, Any]] = []

    def record_table_stat(self, table: str, row_count: int, size_bytes: int) -> None:
        self._table_stats[table] = {"rows": row_count, "size": size_bytes,
                                      "updated_at": time.time()}

    def record_query_stat(self, sql: str, execution_ms: float, rows_affected: int) -> None:
        self._query_stats.append({"sql": sql[:200], "time": execution_ms,
                                   "rows": rows_affected, "timestamp": time.time()})
        if len(self._query_stats) > 10000:
            self._query_stats = self._query_stats[-10000:]

    def get_table_stat(self, table: str) -> Dict[str, Any]:
        return self._table_stats.get(table, {})

    def get_slow_queries(self, threshold_ms: float = 100.0) -> List[Dict[str, Any]]:
        return [q for q in self._query_stats if q["time"] > threshold_ms]

    def get_all_table_stats(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._table_stats)

    def stats(self) -> Dict[str, Any]:
        return {"tables": len(self._table_stats), "queries": len(self._query_stats)}
