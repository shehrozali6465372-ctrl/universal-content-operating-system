"""Safety tests for the one-shot Neon migration runner."""
import pytest

from layers.layer13_persistence.modules.postgresql.neon_migration import (
    _source_dsn,
    migrate_to_neon,
)


def _clear_db_env(monkeypatch):
    for key in (
        "POSTGRES_HOST", "PG_HOST", "POSTGRES_DB", "PG_DATABASE",
        "POSTGRES_USER", "PG_USER", "POSTGRES_PASSWORD", "PG_PASSWORD",
        "POSTGRES_PORT", "PG_PORT", "POSTGRES_SSLMODE",
        "UCOS_SOURCE_DATABASE_URL", "DATABASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_source_dsn_uses_canonical_l13_environment(monkeypatch):
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_HOST", "db.internal")
    monkeypatch.setenv("POSTGRES_DB", "ucos")
    monkeypatch.setenv("POSTGRES_USER", "ucos_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test-secret-not-logged")
    dsn = _source_dsn()
    assert "host=db.internal" in dsn
    assert "dbname=ucos" in dsn
    assert "user=ucos_user" in dsn


def test_source_dsn_fails_closed_without_source_configuration(monkeypatch):
    _clear_db_env(monkeypatch)
    with pytest.raises(RuntimeError, match="source PostgreSQL settings are not configured"):
        _source_dsn()


def test_migration_requires_target_before_opening_any_database(monkeypatch):
    _clear_db_env(monkeypatch)
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="NEON_DATABASE_URL"):
        migrate_to_neon()
