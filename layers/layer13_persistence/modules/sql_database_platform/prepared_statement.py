"""prepared_statement.py — Prepared statement management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class PreparedStatement:
    """A prepared SQL statement."""
    __slots__ = ("stmt_id", "sql", "parameters", "created_at", "execution_count")
    _counter = 0

    def __init__(self, sql: str, parameters: List[str] = None) -> None:
        PreparedStatement._counter += 1
        self.stmt_id: int = PreparedStatement._counter
        self.sql = sql
        self.parameters = parameters or []
        self.created_at: float = time.time()
        self.execution_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"stmt_id": self.stmt_id, "sql": self.sql[:200],
                "parameters": self.parameters, "executions": self.execution_count}


class PreparedStatementManager:
    """Manages prepared statements."""

    def __init__(self) -> None:
        self._statements: Dict[str, PreparedStatement] = {}

    def prepare(self, name: str, sql: str, parameters: List[str] = None) -> PreparedStatement:
        stmt = PreparedStatement(sql, parameters)
        self._statements[name] = stmt
        return stmt

    def get(self, name: str) -> Optional[PreparedStatement]:
        return self._statements.get(name)

    def execute(self, name: str, params: Dict[str, Any] = None) -> bool:
        stmt = self._statements.get(name)
        if stmt:
            stmt.execution_count += 1
            return True
        return False

    def drop(self, name: str) -> bool:
        if name in self._statements:
            del self._statements[name]
            return True
        return False

    def list_all(self) -> List[PreparedStatement]:
        return list(self._statements.values())

    def stats(self) -> Dict[str, Any]:
        total_exec = sum(s.execution_count for s in self._statements.values())
        return {"statements": len(self._statements), "total_executions": total_exec}
