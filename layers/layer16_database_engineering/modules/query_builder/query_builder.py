"""Parameterized SQL query builder with strict identifier validation."""
from __future__ import annotations
import re
from typing import Any, List, Optional, Tuple

class QueryBuilder:
    _IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
    _OPS = {"=", "!=", "<", "<=", ">", ">=", "LIKE", "ILIKE", "IS", "IS NOT"}
    _JOIN_TYPES = {"INNER", "LEFT", "RIGHT", "FULL", "CROSS"}

    @classmethod
    def _identifier(cls, value: str) -> str:
        if value == "*": return value
        if not isinstance(value, str) or not cls._IDENT.fullmatch(value):
            raise ValueError(f"unsafe SQL identifier: {value!r}")
        return value

    def __init__(self, table: str = "") -> None:
        self._table = self._identifier(table) if table else ""
        self._select_fields = ["*"]
        self._where_clauses: List[Tuple[str, str, Any]] = []
        self._order_by: List[Tuple[str, str]] = []
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._group_by: List[str] = []
        self._having: List[Tuple[str, str, Any]] = []
        self._joins: List[Tuple[str, str, str]] = []
        self._params: List[Any] = []

    def table(self, name: str) -> "QueryBuilder":
        self._table = self._identifier(name); return self

    def select(self, *fields: str) -> "QueryBuilder":
        if not fields: raise ValueError("select requires at least one field")
        self._select_fields = [self._identifier(f) for f in fields]; return self

    def where(self, field: str, op: str, value: Any) -> "QueryBuilder":
        op = op.upper()
        if op not in self._OPS: raise ValueError("unsupported SQL operator")
        self._where_clauses.append((self._identifier(field), op, value)); return self

    def where_eq(self, field: str, value: Any) -> "QueryBuilder":
        return self.where(field, "=", value)

    def where_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        self._where_clauses.append((self._identifier(field), "IN", list(values))); return self

    def order_by(self, field: str, direction: str = "ASC") -> "QueryBuilder":
        direction = direction.upper()
        if direction not in {"ASC", "DESC"}: raise ValueError("invalid order direction")
        self._order_by.append((self._identifier(field), direction)); return self

    def limit(self, n: int) -> "QueryBuilder":
        if n < 0: raise ValueError("limit cannot be negative")
        self._limit_val = n; return self

    def offset(self, n: int) -> "QueryBuilder":
        if n < 0: raise ValueError("offset cannot be negative")
        self._offset_val = n; return self

    def group_by(self, *fields: str) -> "QueryBuilder":
        self._group_by = [self._identifier(f) for f in fields]; return self

    def having(self, field: str, op: str, value: Any) -> "QueryBuilder":
        op = op.upper()
        if op not in self._OPS: raise ValueError("unsupported SQL operator")
        self._having.append((self._identifier(field), op, value)); return self

    def join(self, table: str, on: str, join_type: str = "INNER") -> "QueryBuilder":
        join_type = join_type.upper()
        if join_type not in self._JOIN_TYPES: raise ValueError("invalid join type")
        if not on or any(token in on for token in (";", "--", "/*", "*/")):
            raise ValueError("unsafe join condition")
        self._joins.append((self._identifier(table), on, join_type)); return self

    def build(self) -> str:
        if not self._table: raise ValueError("table is required")
        params: List[Any] = []
        parts = [f"SELECT {', '.join(self._select_fields)} FROM {self._table}"]
        for table, on, join_type in self._joins:
            parts.append(f"{join_type} JOIN {table} ON {on}")
        if self._where_clauses:
            conditions = []
            for field, op, value in self._where_clauses:
                if op == "IN":
                    if not value: conditions.append("1 = 0")
                    else:
                        conditions.append(f"{field} IN ({', '.join('?' for _ in value)})")
                        params.extend(value)
                elif op in {"IS", "IS NOT"} and value is None:
                    conditions.append(f"{field} {op} NULL")
                else:
                    conditions.append(f"{field} {op} ?"); params.append(value)
            parts.append("WHERE " + " AND ".join(conditions))
        if self._group_by: parts.append("GROUP BY " + ", ".join(self._group_by))
        if self._having:
            parts.append("HAVING " + " AND ".join(f"{f} {o} ?" for f, o, _ in self._having))
            params.extend(v for _, _, v in self._having)
        if self._order_by:
            parts.append("ORDER BY " + ", ".join(f"{f} {d}" for f, d in self._order_by))
        if self._limit_val is not None: parts.append(f"LIMIT {self._limit_val}")
        if self._offset_val is not None: parts.append(f"OFFSET {self._offset_val}")
        self._params = params
        return " ".join(parts)

    def build_params(self) -> List[Any]:
        self.build(); return list(self._params)

    def reset(self) -> "QueryBuilder":
        self._select_fields = ["*"]; self._where_clauses.clear()
        self._order_by.clear(); self._limit_val = self._offset_val = None
        self._group_by.clear(); self._having.clear(); self._joins.clear(); self._params.clear()
        return self
