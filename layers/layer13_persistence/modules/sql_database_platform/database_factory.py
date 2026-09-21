"""database_factory.py — Database engine factory."""
from __future__ import annotations
from typing import Optional
from layers.layer13_persistence.modules.sql_database_platform.database_engine import DatabaseEngine


class DatabaseFactory:
    """Creates database engine instances."""

    _engines = {"postgresql", "sqlite"}

    @classmethod
    def create(cls, engine_type: str) -> Optional[DatabaseEngine]:
        normalized = str(engine_type).strip().lower()
        if normalized not in cls._engines:
            raise ValueError(f"unsupported database engine: {normalized}")
        return DatabaseEngine(normalized)

    @classmethod
    def supported(cls) -> list:
        return sorted(cls._engines)
