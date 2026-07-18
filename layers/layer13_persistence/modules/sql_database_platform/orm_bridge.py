"""orm_bridge.py — ORM bridge for different frameworks."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ORMModel:
    """Represents an ORM model definition."""
    __slots__ = ("name", "table_name", "fields", "indexes", "metadata")

    def __init__(self, name: str, table_name: str = "") -> None:
        self.name = name
        self.table_name = table_name or name.lower() + "s"
        self.fields: Dict[str, str] = {}
        self.indexes: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def add_field(self, name: str, field_type: str) -> None:
        self.fields[name] = field_type

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "table": self.table_name,
                "fields": dict(self.fields), "indexes": self.indexes}


class ORMBridge:
    """Bridge between persistence system and ORM frameworks."""

    def __init__(self) -> None:
        self._models: Dict[str, ORMModel] = {}
        self._framework: str = "sqlalchemy"

    def set_framework(self, framework: str) -> None:
        self._framework = framework

    def register_model(self, model: ORMModel) -> None:
        self._models[model.name] = model

    def get_model(self, name: str) -> Optional[ORMModel]:
        return self._models.get(name)

    def to_create_table(self, model_name: str) -> str:
        model = self._models.get(model_name)
        if not model:
            return ""
        fields = ", ".join(f"{k} {v}" for k, v in model.fields.items())
        return f"CREATE TABLE {model.table_name} ({fields});"

    def get_all_models(self) -> List[ORMModel]:
        return list(self._models.values())
