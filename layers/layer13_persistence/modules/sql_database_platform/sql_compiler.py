"""sql_compiler.py — SQL compilation."""
from __future__ import annotations
from typing import Any, Dict, List


class SQLCompiler:
    """Compiles abstract operations to SQL."""

    def compile_select(self, table: str, columns: List[str] = None,
                       where: Dict[str, Any] = None) -> str:
        cols = ", ".join(columns or ["*"])
        sql = f"SELECT {cols} FROM {table}"
        if where:
            conditions = [f"{k} = :{k}" for k in where]
            sql += " WHERE " + " AND ".join(conditions)
        return sql

    def compile_insert(self, table: str, data: Dict[str, Any]) -> str:
        cols = ", ".join(data.keys())
        vals = ", ".join(f":{k}" for k in data)
        return f"INSERT INTO {table} ({cols}) VALUES ({vals})"

    def compile_update(self, table: str, data: Dict[str, Any],
                       where: Dict[str, Any]) -> str:
        sets = ", ".join(f"{k} = :{k}" for k in data)
        conditions = [f"{k} = :w_{k}" for k in where]
        return f"UPDATE {table} SET {sets} WHERE " + " AND ".join(conditions)

    def compile_delete(self, table: str, where: Dict[str, Any]) -> str:
        conditions = [f"{k} = :{k}" for k in where]
        return f"DELETE FROM {table} WHERE " + " AND ".join(conditions)
