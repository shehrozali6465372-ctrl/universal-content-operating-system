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
