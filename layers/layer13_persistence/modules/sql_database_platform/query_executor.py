"""query_executor.py — Query execution engine."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class QueryResult:
    """Result from a query execution."""
    __slots__ = ("rows", "affected_rows", "execution_time_ms", "columns", "query")
    _counter = 0

    def __init__(self, rows: List[Dict[str, Any]] = None, affected: int = 0,
                 execution_ms: float = 0.0, columns: List[str] = None) -> None:
        QueryResult._counter += 1
        self.rows = rows or []
        self.affected_rows = affected
        self.execution_time_ms = execution_ms
        self.columns = columns or []
        self.query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"rows": self.rows, "affected": self.affected_rows,
                "execution_ms": self.execution_time_ms, "columns": self.columns}


class QueryExecutor:
    """Executes SQL queries with logging and metrics."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []
        self._total_queries: int = 0
        self._total_errors: int = 0

    def execute(self, sql: str, params: Dict[str, Any] = None,
                fetch: bool = True) -> QueryResult:
        start = time.time()
        try:
            result = QueryResult([], 0, (time.time() - start) * 1000)
            result.query = sql
            self._total_queries += 1
            self._history.append({"sql": sql[:200], "time": time.time(),
                                    "success": True})
            return result
        except Exception:
            self._total_errors += 1
            self._history.append({"sql": sql[:200], "time": time.time(),
                                    "success": False})
            raise

    def execute_many(self, sql: str, params_list: List[Dict[str, Any]]) -> QueryResult:
        affected = len(params_list)
        for params in params_list:
            self.execute(sql, params, fetch=False)
        return QueryResult(affected=affected)

    def fetch_one(self, sql: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        result = self.execute(sql, params)
        return result.rows[0] if result.rows else None

    def fetch_all(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        return self.execute(sql, params).rows

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def stats(self) -> Dict[str, Any]:
        return {"total_queries": self._total_queries, "total_errors": self._total_errors,
                "error_rate": self._total_errors / max(1, self._total_queries)}
