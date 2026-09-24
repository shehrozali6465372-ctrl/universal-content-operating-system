import pytest

from layers.layer01_core.modules.scheduler.task_queue import (
    Task,
    TaskQueue,
    TaskStatus,
)


def test_claim_restores_pending_state_when_persistence_fails():
    queue = TaskQueue()
    task = Task(name="claim", job_type="test")
    queue._tasks[task.task_id] = task
    original_save = queue._save
    queue._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            queue.claim(task.task_id)
        assert task.status is TaskStatus.PENDING
    finally:
        queue._save = original_save


def test_next_task_restores_pending_state_when_persistence_fails():
    queue = TaskQueue()
    task = Task(name="next", job_type="test")
    queue._tasks[task.task_id] = task
    original_save = queue._save
    queue._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            queue.next_task()
        assert task.status is TaskStatus.PENDING
    finally:
        queue._save = original_save


def test_status_update_restores_previous_state_when_persistence_fails():
    queue = TaskQueue()
    task = Task(name="status", job_type="test")
    queue._tasks[task.task_id] = task
    original_save = queue._save
    queue._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            queue.update_status(task.task_id, TaskStatus.RUNNING)
        assert task.status is TaskStatus.PENDING
    finally:
        queue._save = original_save


def test_replay_restores_terminal_state_when_persistence_fails():
    queue = TaskQueue()
    task = Task(name="replay", job_type="test", status=TaskStatus.FAILED)
    queue._tasks[task.task_id] = task
    original_save = queue._save
    queue._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            queue.replay(task.task_id)
        assert task.status is TaskStatus.FAILED
    finally:
        queue._save = original_save


def test_cancel_restores_previous_state_when_persistence_fails():
    queue = TaskQueue()
    task = Task(name="cancel", job_type="test")
    queue._tasks[task.task_id] = task
    original_save = queue._save
    queue._save = lambda: (_ for _ in ()).throw(OSError("disk full"))
    try:
        with pytest.raises(OSError, match="disk full"):
            queue.cancel(task.task_id)
        assert task.status is TaskStatus.PENDING
    finally:
        queue._save = original_save
