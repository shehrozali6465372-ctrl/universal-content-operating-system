"""
Tests for Database Manager Module
Layer 1: Core System — Module 4

Run: python -m pytest layers/layer01_core/tests/test_database_manager.py -v
"""

import pytest
import sqlite3
from layers.layer01_core.modules.database_manager import DatabaseManager
from layers.layer01_core.modules.models import get_all_table_names
from layers.layer01_core.modules.migrations import MigrationRegistry


@pytest.fixture
def db(tmp_path):
    """Create and initialize a fresh database for each test."""
    manager = DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        project_root=str(tmp_path),
    )
    manager.initialize()
    yield manager
    manager.close()


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


# ── Test 1: Initialization ─────────────────

class TestInitialization:
    def test_creates_database_file(self, db):
        assert db.db_path.exists()

    def test_tables_created(self, db):
        tables = db.get_tables()
        expected = get_all_table_names()
        for name in expected:
            assert name in tables

    def test_is_initialized_flag(self, db):
        assert db.is_initialized is True

    def test_schema_version_table_exists(self, db):
        assert db.table_exists("schema_version")


# ── Test 2: Migrations ─────────────────────

class TestMigrations:
    def test_initial_migration_version(self, db):
        version = db._migration_manager.get_current_version()
        assert version >= 1

    def test_migration_history(self, db):
        history = db._migration_manager.migration_history()
        assert len(history) >= 1
        assert history[0]["version"] == 1

    def test_no_pending_migrations_after_init(self, db):
        pending = db._migration_manager.get_pending_migrations()
        assert len(pending) == 0

    def test_migration_registry(self):
        registry = MigrationRegistry()
        registry.register(1, "First", "CREATE TABLE t1 (id INTEGER PRIMARY KEY);")
        registry.register(2, "Second", "CREATE TABLE t2 (id INTEGER PRIMARY KEY);")
        pending = registry.get_pending(0)
        assert len(pending) == 2
        pending_after_v1 = registry.get_pending(1)
        assert len(pending_after_v1) == 1


# ── Test 3: Insert ─────────────────────────

class TestInsert:
    def test_insert_single_row(self, db):
        row_id = db.insert("agent_config", {"key": "app_name", "value": "TestApp"})
        assert row_id is not None

    def test_insert_and_query(self, db):
        db.insert("agent_config", {"key": "test_key", "value": "test_value"})
        rows = db.query("SELECT * FROM agent_config WHERE key = ?", ("test_key",))
        assert len(rows) == 1
        assert rows[0]["value"] == "test_value"

    def test_insert_multiple(self, db):
        rows = [
            {"level": "INFO", "module": "test", "message": "msg1"},
            {"level": "ERROR", "module": "test", "message": "msg2"},
            {"level": "DEBUG", "module": "test", "message": "msg3"},
        ]
        count = db.insert_many("agent_logs", rows)
        assert count == 3
        assert db.count("agent_logs") == 3


# ── Test 4: Query ──────────────────────────

class TestQuery:
    def test_query_returns_dicts(self, db):
        db.insert("agent_config", {"key": "k1", "value": "v1"})
        rows = db.query("SELECT * FROM agent_config")
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)

    def test_query_one(self, db):
        db.insert("agent_config", {"key": "only", "value": "one"})
        row = db.query_one("SELECT * FROM agent_config WHERE key = ?", ("only",))
        assert row is not None
        assert row["value"] == "one"

    def test_query_one_returns_none(self, db):
        row = db.query_one("SELECT * FROM agent_config WHERE key = ?", ("nonexistent",))
        assert row is None

    def test_query_empty_result(self, db):
        rows = db.query("SELECT * FROM agent_config WHERE key = ?", ("none",))
        assert rows == []


# ── Test 5: Update ─────────────────────────

class TestUpdate:
    def test_update_row(self, db):
        db.insert("agent_config", {"key": "k1", "value": "old"})
        affected = db.update("agent_config", {"value": "new"}, "key = ?", ("k1",))
        assert affected == 1
        row = db.query_one("SELECT * FROM agent_config WHERE key = ?", ("k1",))
        assert row["value"] == "new"


# ── Test 6: Delete ─────────────────────────

class TestDelete:
    def test_delete_row(self, db):
        db.insert("agent_config", {"key": "to_delete", "value": "gone"})
        assert db.count("agent_config", "key = ?", ("to_delete",)) == 1
        affected = db.delete("agent_config", "key = ?", ("to_delete",))
        assert affected == 1
        assert db.count("agent_config", "key = ?", ("to_delete",)) == 0


# ── Test 7: Count ──────────────────────────

class TestCount:
    def test_count_empty(self, db):
        assert db.count("agent_config") == 0

    def test_count_with_data(self, db):
        db.insert("agent_config", {"key": "a", "value": "1"})
        db.insert("agent_config", {"key": "b", "value": "2"})
        assert db.count("agent_config") == 2

    def test_count_with_where(self, db):
        db.insert("agent_logs", {"level": "INFO", "module": "m", "message": "1"})
        db.insert("agent_logs", {"level": "ERROR", "module": "m", "message": "2"})
        assert db.count("agent_logs", "level = ?", ("INFO",)) == 1


# ── Test 8: Transactions ───────────────────

class TestTransactions:
    def test_transaction_commit(self, db):
        with db.transaction():
            db.insert("agent_config", {"key": "in_tx", "value": "committed"})
        assert db.count("agent_config", "key = ?", ("in_tx",)) == 1

    def test_transaction_rollback(self, db):
        try:
            with db.transaction():
                db.insert("agent_config", {"key": "rollback", "value": "x"})
                raise ValueError("Force rollback")
        except ValueError:
            pass
        assert db.count("agent_config", "key = ?", ("rollback",)) == 0


# ── Test 9: Backup & Restore ───────────────

class TestBackupRestore:
    def test_backup_creates_file(self, db):
        db.insert("agent_config", {"key": "bk", "value": "backup_test"})
        backup = db.backup("backups/test_backup.db")
        assert backup.exists()

    def test_backup_contains_data(self, db):
        db.insert("agent_config", {"key": "bk2", "value": "data"})
        backup = db.backup("backups/bk2.db")
        conn = sqlite3.connect(str(backup))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM agent_config").fetchall()
        assert len(rows) >= 1
        conn.close()

    def test_restore(self, db, tmp_path):
        db.insert("agent_config", {"key": "restore", "value": "original"})
        db.backup("backups/to_restore.db")
        db.close()
        db.restore(str(tmp_path / "backups" / "to_restore.db"))
        rows = db.query("SELECT * FROM agent_config WHERE key = ?", ("restore",))
        assert len(rows) == 1
        assert rows[0]["value"] == "original"

    def test_restore_missing_file_raises(self, db):
        with pytest.raises(FileNotFoundError):
            db.restore("backups/nonexistent.db")


# ── Test 10: Health Check ──────────────────

class TestHealthCheck:
    def test_health_check_pass(self, db):
        report = db.health_check()
        assert report["overall"] == "PASS"
        assert report["checks"]["connection"]["status"] == "PASS"
        assert report["checks"]["tables"]["status"] == "PASS"

    def test_health_check_includes_stats(self, db):
        report = db.health_check()
        assert "file_size" in report["checks"]


# ── Test 11: Stats ─────────────────────────

class TestStats:
    def test_get_stats(self, db):
        db.insert("agent_config", {"key": "s1", "value": "v1"})
        stats = db.get_stats()
        assert stats["tables"] >= 8
        assert stats["total_rows"] >= 1
        assert stats["db_size_kb"] >= 0
