"""Bounded, thread-safe runtime checkpoints."""
from __future__ import annotations

import itertools
import threading
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional

_COUNTER = itertools.count(1)


class RuntimeCheckpoint:
    __slots__ = ("checkpoint_id", "state", "data", "created_at")

    def __init__(self, checkpoint_id: str, state: str) -> None:
        self.checkpoint_id = checkpoint_id
        self.state = state
        self.data: Dict[str, Any] = {}
        self.created_at = time.time()


class RuntimeMemory:
    def __init__(self, max_checkpoints: int = 100) -> None:
        if isinstance(max_checkpoints, bool) or not isinstance(max_checkpoints, int) or max_checkpoints < 1:
            raise ValueError("max_checkpoints must be a positive integer")
        self._max = max_checkpoints
        self._checkpoints: List[RuntimeCheckpoint] = []
        self._lock = threading.RLock()

    def save_checkpoint(
        self, state: str, data: Optional[Dict[str, Any]] = None
    ) -> RuntimeCheckpoint:
        if not isinstance(state, str) or not state:
            raise ValueError("state must be non-empty")
        if data is not None and not isinstance(data, dict):
            raise TypeError("data must be a dict")
        checkpoint = RuntimeCheckpoint(
            f"cp_{time.time_ns()}_{next(_COUNTER)}", state
        )
        if data is not None:
            checkpoint.data = deepcopy(data)
        with self._lock:
            self._checkpoints.append(checkpoint)
            if len(self._checkpoints) > self._max:
                del self._checkpoints[:-self._max]
        return deepcopy(checkpoint)

    def get_latest(self) -> Optional[RuntimeCheckpoint]:
        with self._lock:
            return deepcopy(self._checkpoints[-1]) if self._checkpoints else None

    def get_all(self) -> List[RuntimeCheckpoint]:
        with self._lock:
            return deepcopy(self._checkpoints)

    def clear(self) -> int:
        with self._lock:
            count = len(self._checkpoints)
            self._checkpoints.clear()
            return count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_checkpoints": len(self._checkpoints),
                "max_capacity": self._max,
            }
