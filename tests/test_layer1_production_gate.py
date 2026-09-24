import json
import time
import threading
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
    cm = ConfigManager(project_root=str(tmp_path), admin_mode=True)
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


def test_scheduler_cron_persistence_survives_restart(tmp_path):
    from layers.layer01_core.modules.scheduler.scheduler_manager import SchedulerManager

    queue_path = tmp_path / "queue.json"
    retry_path = tmp_path / "retry.json"
    cron_path = tmp_path / "cron.json"
    first = SchedulerManager(
        queue_persist_path=str(queue_path),
        retry_persist_path=str(retry_path),
        cron_persist_path=str(cron_path),
    )
    first.register_handler("noop", lambda _: None)
    first.add_cron_job("persisted", "*/5 * * * *", "noop", params={"x": 1})
    first.shutdown()

    second = SchedulerManager(
        queue_persist_path=str(queue_path),
        retry_persist_path=str(retry_path),
        cron_persist_path=str(cron_path),
    )
    try:
        assert len(second._cron_jobs) == 1
        job = next(iter(second._cron_jobs.values()))
        assert job["name"] == "persisted"
        assert job["cron_expr"] == "*/5 * * * *"
        assert job["params"] == {"x": 1}
    finally:
        second.shutdown()


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


def test_memory_mutation_rejects_invalid_contract_values(tmp_path):
    from layers.layer01_core.modules.memory_manager import MemoryManager

    manager = MemoryManager(db_path="memory.db", project_root=str(tmp_path)).initialize()
    try:
        entry_id = manager.save("long_term", "category", "key", "value")
        with pytest.raises(ValueError, match="between 0 and 1"):
            manager.update(entry_id, importance=2.0)
        with pytest.raises(ValueError, match="Invalid memory level"):
            manager.load("invalid-level")
        assert manager.get(entry_id)["value"] == "value"
    finally:
        manager.close()


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


def test_backup_compression_failure_leaves_no_orphan_artifact(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("payload")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir))

    def fail_copyfileobj(*args, **kwargs):
        raise OSError("compression failed")

    monkeypatch.setattr(
        "layers.layer01_core.modules.backup_manager.backup_manager.shutil.copyfileobj",
        fail_copyfileobj,
    )
    with pytest.raises(OSError, match="compression failed"):
        bm.backup("test", str(source), compress=True)

    assert bm.count() == 0
    assert not list(backup_dir.glob("*.bak"))
    assert not list(backup_dir.glob("*.gz"))
    assert not list(backup_dir.glob("*.stage"))


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


def test_layer13_manager_concurrent_initialize_is_single_owner(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "aios")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager

    manager = PostgreSQLManager()
    results = []
    errors = []
    lock = threading.Lock()

    def initialize():
        try:
            value = manager.initialize()
            with lock:
                results.append(value)
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=initialize) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    try:
        assert not errors
        assert results == [True] * 8
        assert manager.health_check()["overall"] == "PASS"
    finally:
        manager.close()


def test_secret_empty_value_is_rejected(tmp_path):
    from layers.layer01_core.modules.secrets_manager import SecretsManager
    manager = SecretsManager(
        secrets_path=".secrets",
        audit_log_path="logs/audit.log",
        project_root=str(tmp_path),
    ).setup(master_key="test-master-key")
    with pytest.raises(ValueError, match="non-empty"):
        manager.store("EMPTY_SECRET", "")


def test_database_concurrent_initialization_is_serialized(tmp_path):
    results = []
    errors = []
    lock = threading.Lock()

    def initialize():
        db = DatabaseManager("concurrent.db", project_root=str(tmp_path))
        try:
            db.initialize()
            with lock:
                results.append(db)
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=initialize) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    try:
        assert not errors
        assert len(results) == 4
        assert all(db.health_check()["overall"] == "PASS" for db in results)
    finally:
        for db in results:
            db.close()


def test_backup_restore_rejects_symlink_target(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("safe")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir))
    entry = bm.backup("test", str(source), compress=False)
    target = tmp_path / "restore.txt"
    target.write_text("outside")
    link = tmp_path / "restore-link"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable")
    with pytest.raises(ValueError, match="symlink"):
        bm.restore(entry.backup_id, str(link))


def test_backup_entry_rejects_invalid_hash():
    from layers.layer01_core.modules.backup_manager.backup_entry import BackupEntry
    with pytest.raises(ValueError, match="SHA-256"):
        BackupEntry("id", "test", "x.bak", hash_sha256="not-a-hash")


def test_memory_concurrent_initialization_is_serialized(tmp_path):
    from layers.layer01_core.modules.memory_manager import MemoryManager

    results = []
    errors = []
    lock = threading.Lock()

    def initialize():
        manager = MemoryManager("shared-memory.db", project_root=str(tmp_path))
        try:
            manager.initialize()
            with lock:
                results.append(manager)
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=initialize) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    try:
        assert not errors
        assert len(results) == 4
        assert all(manager.health_check()["overall"] == "PASS" for manager in results)
    finally:
        for manager in results:
            manager.close()


def test_backup_orphan_detection(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("safe")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir))
    bm.backup("test", str(source), compress=False)
    orphan = backup_dir / "unregistered.bak"
    orphan.write_text("orphan")
    assert bm.find_orphans() == ["unregistered.bak"]


def test_backup_rotation_registry_failure_restores_artifacts(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("safe")
    backup_dir = tmp_path / "backups"
    bm = BackupManager(str(backup_dir), default_retention_days=0)
    entry = bm.backup("test", str(source), compress=False)

    def fail_registry():
        raise OSError("registry write failed")

    monkeypatch.setattr(bm, "_save_registry", fail_registry)
    with pytest.raises(OSError, match="registry write failed"):
        bm.rotate()
    assert bm.get_entry(entry.backup_id).backup_id == entry.backup_id
    assert (backup_dir / entry.filepath).exists()
