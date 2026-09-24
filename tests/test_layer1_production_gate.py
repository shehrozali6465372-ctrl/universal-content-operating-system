import json
import time
from pathlib import Path

import pytest

from layers.layer01_core.modules.validators import validate_api_key
from layers.layer01_core.modules.key_store import KeyStore
from layers.layer01_core.modules.file_manager.file_manager import FileManager
from layers.layer01_core.modules.file_manager.file_cache import FileCache
from layers.layer01_core.modules.migrations import MigrationManager
from layers.layer01_core.modules.database_manager import DatabaseManager
from layers.layer01_core.modules.backup_manager.backup_manager import BackupManager
from layers.layer01_core.modules.scheduler.scheduler_manager import SchedulerManager
from layers.layer01_core.modules.scheduler.task_queue import Task
from layers.layer01_core.modules.logger.logger_manager import LoggerManager


def test_config_persistence_excludes_credentials(tmp_path):
    from layers.layer01_core.modules.config_manager import ConfigManager

    ConfigManager.reset()
    cm = ConfigManager(project_root=str(tmp_path))
    cm.set("OPENAI_API_KEY", "secret-value")
    cm.set("NORMAL_SETTING", "safe-value")
    path = tmp_path / "config.json"
    cm.save(str(path))
    payload = json.loads(path.read_text())
    assert "OPENAI_API_KEY" not in payload
    assert payload["NORMAL_SETTING"] == "safe-value"
    ConfigManager.reset()


def test_credentials_are_provider_neutral():
    validate_api_key("DEEPSEEK_API_KEY", "deepseek-example-token")


def test_corrupt_key_store_fails_closed(tmp_path):
    path = tmp_path / ".secrets"
    path.write_text("{not-json")
    with pytest.raises(ValueError):
        KeyStore(str(path)).load()


def test_file_manager_rejects_traversal_and_restores_atomically(tmp_path):
    fm = FileManager(str(tmp_path))
    fm.write("a.txt", "one", create_backup=False)
    with pytest.raises(ValueError):
        fm.read("../outside.txt")
    fm.write("a.txt", "two", create_backup=False)


def test_file_cache_is_thread_safe():
    cache = FileCache(4)
    for i in range(1000):
        cache.set(str(i % 8), i)
        cache.get(str(i % 8))
    assert cache.size <= 4


def test_database_nested_transactions_remain_atomic(tmp_path):
    db = DatabaseManager("test.db", project_root=str(tmp_path)).initialize()
    try:
        with pytest.raises(RuntimeError, match="force rollback"):
            with db.transaction():
                db.insert("agent_config", {"key": "atomic", "value": "outer"})
                with db.transaction():
                    db.insert("agent_config", {"key": "nested", "value": "inner"})
                raise RuntimeError("force rollback")
        assert db.query_one(
            "SELECT key FROM agent_config WHERE key = ?", ("atomic",)
        ) is None
        assert db.query_one(
            "SELECT key FROM agent_config WHERE key = ?", ("nested",)
        ) is None
    finally:
        db.close()


def test_migration_partial_failure_rolls_back(tmp_path):
    db = DatabaseManager("test.db", project_root=str(tmp_path)).initialize()
    manager = db._migration_manager
    manager._registry.register(3, "intentional failure", "CREATE TABLE transient_table (id INTEGER); THIS IS INVALID SQL;")
    with pytest.raises(RuntimeError):
        manager.migrate()
    assert not db.table_exists("transient_table")
    db.close()


def test_backup_compressed_restore_verifies_payload(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("production payload")
    bm = BackupManager(str(tmp_path / "backups"))
    entry = bm.backup("test", str(source), compress=True)
    assert entry is not None
    assert bm.verify_integrity(entry.backup_id)
    target = tmp_path / "restore.txt"
    assert bm.restore(entry.backup_id, str(target))
    assert target.read_text() == "production payload"

def test_backup_restore_rejects_tampered_artifact(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("protected payload")
    bm = BackupManager(str(tmp_path / "backups"))
    entry = bm.backup("test", str(source), compress=True)
    backup = tmp_path / "backups" / entry.filepath
    with backup.open("ab") as fh:
        fh.write(b"tamper")
    assert bm.verify_integrity(entry.backup_id) is False
    with pytest.raises(Exception, match="Integrity"):
        bm.restore(entry.backup_id, str(tmp_path / "restore.txt"))


def test_scheduler_deduplicates_and_times_out():
    scheduler = SchedulerManager()
    scheduler.register_handler("slow", lambda _: time.sleep(2))
    first = scheduler.add_task("same", "slow", timeout_seconds=1, max_retries=0)
    second = scheduler.add_task("same", "slow", timeout_seconds=1, max_retries=0)
    assert first == second
    result = scheduler.run_next()
    assert result["status"] == "FAILED"
    assert "timed out" in result["error"].lower()
    scheduler.shutdown()


def test_logger_redacts_sensitive_details(tmp_path):
    LoggerManager.reset()
    logger = LoggerManager(log_dir=str(tmp_path), enable_console=False)
    entry = logger.info("test", "credential operation", api_key="secret-value", normal="ok")
    assert entry["details"]["api_key"] == "***REDACTED***"
    raw = (tmp_path / "agent.log").read_text()
    assert "secret-value" not in raw
    LoggerManager.reset()


def test_memory_snapshot_rejects_count_mismatch(tmp_path):
    from layers.layer01_core.modules.memory_manager import MemoryManager
    manager = MemoryManager(db_path="memory.db", project_root=str(tmp_path)).initialize()
    snapshot = tmp_path / "bad-memory.json"
    snapshot.write_text(json.dumps({
        "timestamp": "2026-01-01T00:00:00+00:00",
        "levels": {
            "long_term": {
                "count": 2,
                "entries": [{
                    "level": "long_term",
                    "category": "test",
                    "key": "k",
                    "value": "v",
                    "tags": "",
                    "importance": 0.5,
                }],
            }
        },
    }))
    with pytest.raises(ValueError, match="count mismatch"):
        manager.restore(str(snapshot))
    manager.close()


def test_backup_registry_rejects_path_escape(tmp_path):
    from layers.layer01_core.modules.backup_manager.backup_manager import BackupManager
    source = tmp_path / "source.txt"
    source.write_text("safe")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir))
    entry = bm.backup("test", str(source), compress=False)
    registry = json.loads((backup_dir / "_registry.json").read_text())
    registry["entries"][entry.backup_id]["filepath"] = "../outside.txt"
    (backup_dir / "_registry.json").write_text(json.dumps(registry))
    with pytest.raises(RuntimeError, match="unreadable"):
        BackupManager(str(backup_dir))


def test_backup_registry_rejects_key_mismatch(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("safe")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir))
    entry = bm.backup("test", str(source), compress=False)
    registry = json.loads((backup_dir / "_registry.json").read_text())
    payload = registry["entries"].pop(entry.backup_id)
    registry["entries"]["forged-id"] = payload
    (backup_dir / "_registry.json").write_text(json.dumps(registry))
    with pytest.raises(RuntimeError, match="unreadable"):
        BackupManager(str(backup_dir))


def test_backup_copy_failure_leaves_no_partial_artifact(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("payload")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir))

    def fail_copy(*args, **kwargs):
        raise OSError("copy failed")

    monkeypatch.setattr("layers.layer01_core.modules.backup_manager.backup_manager.shutil.copy2", fail_copy)
    with pytest.raises(OSError, match="copy failed"):
        bm.backup("test", str(source), compress=False)

    assert bm.count() == 0
    assert list(backup_dir.glob("*.bak")) == []
    assert list(backup_dir.glob("*.stage")) == []


def test_memory_snapshot_rejects_path_escape(tmp_path):
    from layers.layer01_core.modules.memory_manager import MemoryManager
    manager = MemoryManager(db_path="memory.db", project_root=str(tmp_path)).initialize()
    with pytest.raises(ValueError, match="escapes project root"):
        manager.snapshot("../outside-memory.json")
    assert not (tmp_path.parent / "outside-memory.json").exists()
    manager.close()


def test_layer13_uninitialized_backend_fails_health():
    from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager
    backend = PostgreSQLManager()
    report = backend.health_check()
    assert report["overall"] == "FAIL"
    assert report["initialized"] is False
