"""ContextSync — synchronize context across parallel layer executions."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class SyncBarrier:
    __slots__ = ("barrier_id", "expected", "arrived", "barrier", "released")

    def __init__(self, barrier_id: str, expected: int) -> None:
        self.barrier_id = barrier_id
        self.expected = expected
        self.arrived = 0
        self.barrier = threading.Condition()
        self.released = False

    def wait(self, timeout: float = 30.0) -> bool:
        with self.barrier:
            self.arrived += 1
            if self.arrived >= self.expected:
                self.released = True
                self.barrier.notify_all()
                return True
            return self.barrier.wait(timeout=timeout)


class ContextSync:
    def __init__(self) -> None:
        self._contexts: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._barriers: Dict[str, SyncBarrier] = {}
        self._history: List[Dict[str, Any]] = []

    def create_context(self, context_id: str, initial_data: Optional[Dict[str, Any]] = None) -> None:
        self._contexts[context_id] = dict(initial_data or {})
        self._locks[context_id] = threading.Lock()

    def get(self, context_id: str, key: str) -> Any:
        ctx = self._contexts.get(context_id, {})
        return ctx.get(key)

    def set(self, context_id: str, key: str, value: Any) -> None:
        lock = self._locks.get(context_id)
        if lock:
            with lock:
                if context_id not in self._contexts:
                    self._contexts[context_id] = {}
                self._contexts[context_id][key] = value
                self._history.append({"context": context_id, "key": key, "time": time.time()})

    def merge(self, context_id: str, data: Dict[str, Any]) -> None:
        lock = self._locks.get(context_id)
        if lock:
            with lock:
                self._contexts.setdefault(context_id, {}).update(data)

    def snapshot(self, context_id: str) -> Dict[str, Any]:
        return dict(self._contexts.get(context_id, {}))

    def restore(self, context_id: str, data: Dict[str, Any]) -> None:
        self._contexts[context_id] = dict(data)

    def create_barrier(self, barrier_id: str, expected: int) -> SyncBarrier:
        barrier = SyncBarrier(barrier_id, expected)
        self._barriers[barrier_id] = barrier
        return barrier

    def wait_barrier(self, barrier_id: str, timeout: float = 30.0) -> bool:
        barrier = self._barriers.get(barrier_id)
        if barrier:
            return barrier.wait(timeout)
        return False

    def delete_context(self, context_id: str) -> bool:
        if context_id in self._contexts:
            del self._contexts[context_id]
            self._locks.pop(context_id, None)
            return True
        return False

    def list_contexts(self) -> List[str]:
        return list(self._contexts.keys())

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
