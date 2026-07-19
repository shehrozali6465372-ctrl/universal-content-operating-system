"""QueryBuilder — fluent SQL query construction."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


class QueryBuilder:
    def __init__(self, table: str = "") -> None:
        self._table = table
        self._select_fields: List[str] = ["*"]
        self._where_clauses: List[Tuple[str, str, Any]] = []
        self._order_by: List[Tuple[str, str]] = []
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._group_by: List[str] = []
        self._having: List[Tuple[str, str, Any]] = []
        self._joins: List[Tuple[str, str, str]] = []
        self._params: List[Any] = []

    def table(self, name: str) -> QueryBuilder:
        self._table = name
        return self

    def select(self, *fields: str) -> QueryBuilder:
        self._select_fields = list(fields)
        return self

    def where(self, field: str, op: str, value: Any) -> QueryBuilder:
        self._where_clauses.append((field, op, value))
        self._params.append(value)
        return self

    def where_eq(self, field: str, value: Any) -> QueryBuilder:
        return self.where(field, "=", value)

    def where_in(self, field: str, values: List[Any]) -> QueryBuilder:
        self._where_clauses.append((field, "IN", values))
        self._params.extend(values)
        return self

    def order_by(self, field: str, direction: str = "ASC") -> QueryBuilder:
        self._order_by.append((field, direction))
        return self

    def limit(self, n: int) -> QueryBuilder:
        self._limit_val = n
        return self

    def offset(self, n: int) -> QueryBuilder:
        self._offset_val = n
        return self

    def group_by(self, *fields: str) -> QueryBuilder:
        self._group_by = list(fields)
        return self

    def join(self, table: str, on: str, join_type: str = "INNER") -> QueryBuilder:
        self._joins.append((table, on, join_type))
        return self

    def build(self) -> str:
        parts = [f"SELECT {', '.join(self._select_fields)} FROM {self._table}"]
        for table, on, jtype in self._joins:
            parts.append(f"{jtype} JOIN {table} ON {on}")
        if self._where_clauses:
            conditions = []
            for field, op, value in self._where_clauses:
                if op == "IN":
                    placeholders = ", ".join(["?" for _ in value])
                    conditions.append(f"{field} IN ({placeholders})")
                else:
                    conditions.append(f"{field} {op} ?")
            parts.append("WHERE " + " AND ".join(conditions))
        if self._group_by:
            parts.append(f"GROUP BY {', '.join(self._group_by)}")
        if self._order_by:
            order = ", ".join(f"{f} {d}" for f, d in self._order_by)
            parts.append(f"ORDER BY {order}")
        if self._limit_val is not None:
            parts.append(f"LIMIT {self._limit_val}")
        if self._offset_val is not None:
            parts.append(f"OFFSET {self._offset_val}")
        return " ".join(parts)

    def build_params(self) -> List[Any]:
        return list(self._params)

    def reset(self) -> QueryBuilder:
        self._select_fields = ["*"]
        self._where_clauses.clear()
        self._order_by.clear()
        self._limit_val = None
        self._offset_val = None
        self._group_by.clear()
        self._having.clear()
        self._joins.clear()
        self._params.clear()
        return self
