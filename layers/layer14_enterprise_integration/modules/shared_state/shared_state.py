"""SharedState — thread-safe shared state for cross-layer communication."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional


class SharedState:
    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._watchers: Dict[str, List[Callable]] = {}
        self._changelog: List[Dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            old = self._state.get(key)
            self._state[key] = value
            self._changelog.append({"key": key, "old": str(old)[:100],
                                    "new": str(value)[:100], "time": time.time()})
            for watcher in self._watchers.get(key, []):
                try:
                    watcher(key, old, value)
                except Exception:
                    pass

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._state

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._state:
                del self._state[key]
                return True
        return False

    def update(self, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self.set(k, v)

    def watch(self, key: str, callback: Callable) -> None:
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = []
            self._watchers[key].append(callback)

    def unwatch(self, key: str, callback: Optional[Callable] = None) -> None:
        with self._lock:
            if callback:
                self._watchers[key] = [w for w in self._watchers.get(key, []) if w != callback]
            else:
                self._watchers.pop(key, None)

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._state.keys())

    def items(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def clear(self) -> int:
        with self._lock:
            count = len(self._state)
            self._state.clear()
            return count

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def restore(self, snapshot: Dict[str, Any]) -> None:
        with self._lock:
            self._state = dict(snapshot)

    def get_changelog(self) -> List[Dict[str, Any]]:
        return list(self._changelog)

    def count(self) -> int:
        with self._lock:
            return len(self._state)
