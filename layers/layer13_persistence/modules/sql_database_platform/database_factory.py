"""database_factory.py — Database engine factory."""
from __future__ import annotations
from typing import Optional
from layers.layer13_persistence.modules.sql_database_platform.database_engine import DatabaseEngine


class DatabaseFactory:
    """Creates database engine instances."""

    _engines = {
        "postgresql": DatabaseEngine("postgresql"),
        "mysql": DatabaseEngine("mysql"),
        "sqlite": DatabaseEngine("sqlite"),
        "mariadb": DatabaseEngine("mariadb"),
    }

    @classmethod
    def create(cls, engine_type: str) -> Optional[DatabaseEngine]:
        if engine_type in cls._engines:
            return DatabaseEngine(engine_type)
        return DatabaseEngine(engine_type)

    @classmethod
    def supported(cls) -> list:
        return list(cls._engines.keys()) + ["sqlserver", "oracle"]
