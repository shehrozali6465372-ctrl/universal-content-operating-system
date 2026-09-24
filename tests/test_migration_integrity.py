import sqlite3

import pytest

from layers.layer01_core.modules.migrations import MigrationManager


def make_manager(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "db.sqlite"))
    manager = MigrationManager(conn)
    return conn, manager


def test_missing_migration_version_is_rejected(tmp_path):
    conn, manager = make_manager(tmp_path)
    manager.migrate()
    conn.execute("DELETE FROM schema_version WHERE version = 1")
    conn.commit()
    with pytest.raises(RuntimeError, match="contiguous"):
        manager.get_current_version()
    conn.close()


def test_unknown_migration_version_is_rejected(tmp_path):
    conn, manager = make_manager(tmp_path)
    manager.migrate()
    conn.execute("UPDATE schema_version SET version = 99 WHERE version = 2")
    conn.commit()
    with pytest.raises(RuntimeError, match="contiguous|unknown"):
        manager.get_current_version()
    conn.close()


def test_invalid_migration_version_type_is_rejected(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "db.sqlite"))
    conn.execute(
        "CREATE TABLE schema_version (version TEXT PRIMARY KEY, description TEXT, applied_at TEXT)"
    )
    conn.execute(
        "INSERT INTO schema_version(version, description) VALUES ('bad', 'corrupt')"
    )
    conn.commit()
    manager = MigrationManager(conn)
    with pytest.raises(RuntimeError, match="positive integer"):
        manager.get_current_version()
    conn.close()


def test_non_contiguous_history_is_rejected(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "db.sqlite"))
    conn.execute(
        "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, description TEXT, applied_at TEXT)"
    )
    conn.executemany(
        "INSERT INTO schema_version(version, description) VALUES (?, ?)",
        [(1, "initial"), (3, "future")],
    )
    conn.commit()
    manager = MigrationManager(conn)
    with pytest.raises(RuntimeError, match="contiguous"):
        manager.get_current_version()
    conn.close()


def test_migration_failure_rolls_back_schema_and_history(tmp_path):
    conn, manager = make_manager(tmp_path)
    manager._registry.register(
        3,
        "failing migration",
        "CREATE TABLE temporary_test (id INTEGER PRIMARY KEY); INVALID SQL;",
    )
    with pytest.raises(RuntimeError, match="Migration v3 failed"):
        manager.migrate()
    assert conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='temporary_test'"
    ).fetchone() is None
    assert conn.execute(
        "SELECT version FROM schema_version ORDER BY version"
    ).fetchall() == [(1,), (2,)]
    conn.close()


def test_concurrent_migration_managers_do_not_corrupt_history(tmp_path):
    import threading

    path = tmp_path / "shared.sqlite"
    errors = []

    def migrate():
        conn = sqlite3.connect(str(path), timeout=10)
        try:
            MigrationManager(conn).migrate()
        except Exception as exc:
            errors.append(exc)
        finally:
            conn.close()

    threads = [threading.Thread(target=migrate) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    conn = sqlite3.connect(str(path))
    try:
        versions = [row[0] for row in conn.execute(
            "SELECT version FROM schema_version ORDER BY version"
        )]
        assert versions == [1, 2]
    finally:
        conn.close()
