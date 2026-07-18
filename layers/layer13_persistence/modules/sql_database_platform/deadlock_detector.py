"""deadlock_detector.py — Deadlock detection."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Set


class LockRequest:
    """A lock request."""
    __slots__ = ("transaction_id", "resource", "lock_type", "timestamp")

    def __init__(self, transaction_id: str, resource: str, lock_type: str = "shared") -> None:
        self.transaction_id = transaction_id
        self.resource = resource
        self.lock_type = lock_type
        self.timestamp: float = time.time()


class DeadlockDetector:
    """Detects potential deadlocks in lock requests."""

    def __init__(self) -> None:
        self._requests: List[LockRequest] = []
        self._deadlocks_found: int = 0

    def add_request(self, request: LockRequest) -> None:
        self._requests.append(request)

    def detect(self) -> List[List[str]]:
        waits: Dict[str, Set[str]] = {}
        for req in self._requests:
            if req.lock_type == "exclusive":
                if req.resource not in waits:
                    waits[req.resource] = set()
                waits[req.resource].add(req.transaction_id)
        deadlocks: List[List[str]] = []
        for resource, holders in waits.items():
            if len(holders) > 1:
                deadlocks.append(list(holders))
                self._deadlocks_found += 1
        return deadlocks

    def clear(self) -> None:
        self._requests.clear()

    def stats(self) -> Dict[str, Any]:
        return {"pending_requests": len(self._requests),
                "deadlocks_found": self._deadlocks_found}
