"""SchemaValidator — validate database schemas and table structures."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from enum import Enum


class ColumnType(str, Enum):
    TEXT = "text"; INTEGER = "integer"; FLOAT = "float"; BOOLEAN = "boolean"
    DATETIME = "datetime"; JSON = "json"; BLOB = "blob"


class ColumnDef:
    __slots__ = ("name", "column_type", "nullable", "default", "primary_key",
                 "unique", "indexed", "max_length")

    def __init__(self, name: str, column_type: ColumnType = ColumnType.TEXT,
                 nullable: bool = True, default: Any = None,
                 primary_key: bool = False, unique: bool = False,
                 indexed: bool = False, max_length: Optional[int] = None) -> None:
        self.name = name
        self.column_type = column_type
        self.nullable = nullable
        self.default = default
        self.primary_key = primary_key
        self.unique = unique
        self.indexed = indexed
        self.max_length = max_length

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "type": self.column_type.value,
                "nullable": self.nullable, "primary_key": self.primary_key}


class TableSchema:
    def __init__(self, table_name: str, columns: Optional[List[ColumnDef]] = None) -> None:
        self.table_name = table_name
        self.columns = columns or []

    def add_column(self, column: ColumnDef) -> None:
        self.columns.append(column)

    def get_column(self, name: str) -> Optional[ColumnDef]:
        for c in self.columns:
            if c.name == name:
                return c
        return None


class SchemaValidator:
    def __init__(self) -> None:
        self._schemas: Dict[str, TableSchema] = {}
        self._errors: List[str] = []

    def register_schema(self, schema: TableSchema) -> None:
        self._schemas[schema.table_name] = schema

    def validate(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        schema = self._schemas.get(table_name)
        if not schema:
            return {"valid": False, "errors": [f"Schema not found: {table_name}"]}
        errors = []
        for col in schema.columns:
            if col.name not in data:
                if not col.nullable and col.default is None:
                    errors.append(f"Missing required column: {col.name}")
                continue
            val = data[col.name]
            if val is None and not col.nullable:
                errors.append(f"Column {col.name} cannot be null")
            if col.max_length and isinstance(val, str) and len(val) > col.max_length:
                errors.append(f"Column {col.name} exceeds max length {col.max_length}")
        self._errors.extend(errors)
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_batch(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = [self.validate(table_name, r) for r in records]
        invalid = sum(1 for r in results if not r["valid"])
        return {"total": len(records), "valid": len(records) - invalid, "invalid": invalid}

    def get_errors(self) -> List[str]:
        return list(self._errors)

    def list_schemas(self) -> List[str]:
        return list(self._schemas.keys())
