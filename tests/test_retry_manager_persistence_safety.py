import pytest

from layers.layer01_core.modules.scheduler.retry_manager import RetryManager


def test_record_failure_rolls_back_memory_when_persistence_fails():
    manager = RetryManager()
    original_save = manager._save
    manager._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            manager.record_failure("task-1")
        assert manager.get_retry_count("task-1") == 0
    finally:
        manager._save = original_save


def test_record_success_rolls_back_memory_when_persistence_fails():
    manager = RetryManager()
    manager._retries["task-1"] = {"attempts": 2, "last_failure": 1.0}
    original_save = manager._save
    manager._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            manager.record_success("task-1")
        assert manager.get_retry_count("task-1") == 2
    finally:
        manager._save = original_save


def test_clear_rolls_back_memory_when_persistence_fails():
    manager = RetryManager()
    manager._retries["task-1"] = {"attempts": 2, "last_failure": 1.0}
    original_save = manager._save
    manager._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            manager.clear()
        assert manager.get_retry_count("task-1") == 2
    finally:
        manager._save = original_save
