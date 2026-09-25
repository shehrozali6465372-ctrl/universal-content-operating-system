"""HttpRouter — bounded, thread-safe ingress router."""
from __future__ import annotations

import threading
from copy import deepcopy
from typing import Any, Dict, List, Mapping


class HttpRouter:
    """Accept validated payloads; execution is owned by the engine layer."""

    def __init__(self, max_entries: int = 1_000) -> None:
        if isinstance(max_entries, bool) or not isinstance(max_entries, int) or max_entries < 1:
            raise ValueError("max_entries must be a positive integer")
        self._max_entries = max_entries
        self._data: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def process(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        """Record an ingress payload without falsely claiming downstream execution."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping")
        payload = deepcopy(dict(data))
        with self._lock:
            self._data.append(payload)
            if len(self._data) > self._max_entries:
                del self._data[:-self._max_entries]
            return {
                "status": "accepted",
                "processed": False,
                "queued": False,
                "entries": len(self._data),
            }

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"total": len(self._data), "max_entries": self._max_entries}
