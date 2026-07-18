"""query_builder.py — SQL query builder."""
from __future__ import annotations
from typing import Any, Dict, List


class QueryBuilder:
    """Fluent SQL query builder."""

    def __init__(self) -> None:
        self._table: str = ""
        self._select_cols: List[str] = ["*"]
        self._where_clauses: List[str] = []
        self._order_by: List[str] = []
        self._limit_val: int = 0
        self._offset_val: int = 0
        self._joins: List[str] = []
        self._params: Dict[str, Any] = {}

    def table(self, name: str) -> "QueryBuilder":
        self._table = name
        return self

    def select(self, *columns: str) -> "QueryBuilder":
        self._select_cols = list(columns) if columns else ["*"]
        return self

    def where(self, condition: str) -> "QueryBuilder":
        self._where_clauses.append(condition)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        self._order_by.append(f"{column} {direction}")
        return self

    def limit(self, count: int) -> "QueryBuilder":
        self._limit_val = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        self._offset_val = count
        return self

    def join(self, table: str, condition: str) -> "QueryBuilder":
        self._joins.append(f"JOIN {table} ON {condition}")
        return self

    def build(self) -> str:
        cols = ", ".join(self._select_cols)
        sql = f"SELECT {cols} FROM {self._table}"
        for j in self._joins:
            sql += f" {j}"
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)
        if self._limit_val:
            sql += f" LIMIT {self._limit_val}"
        if self._offset_val:
            sql += f" OFFSET {self._offset_val}"
        return sql

    def to_dict(self) -> Dict[str, Any]:
        return {"table": self._table, "sql": self.build()}
