"""PromiseManager — create and manage async promises."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class PromiseState(str, Enum):
    PENDING = "pending"; RESOLVED = "resolved"; REJECTED = "rejected"


class Promise:
    __slots__ = ("promise_id", "name", "state", "result", "error",
                 "callbacks", "errcbs")

    def __init__(self, name: str = "") -> None:
        self.promise_id = str(uuid.uuid4())[:12]
        self.name = name
        self.state = PromiseState.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.callbacks: list = []
        self.errcbs: list = []

    def resolve(self, result: Any = None) -> None:
        if self.state != PromiseState.PENDING:
            return
        self.state = PromiseState.RESOLVED
        self.result = result
        for cb in self.callbacks:
            try:
                cb(result)
            except Exception:
                pass

    def reject(self, error: str) -> None:
        if self.state != PromiseState.PENDING:
            return
        self.state = PromiseState.REJECTED
        self.error = error
        for cb in self.errcbs:
            try:
                cb(error)
            except Exception:
                pass

    def handled(self) -> bool:
        return self.state != PromiseState.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {"promise_id": self.promise_id, "name": self.name,
                "state": self.state.value}


class PromiseManager:
    def __init__(self) -> None:
        self._promises: Dict[str, Promise] = {}

    def create(self, name: str = "") -> Promise:
        p = Promise(name)
        self._promises[p.promise_id] = p
        return p

    def get(self, promise_id: str) -> Optional[Promise]:
        return self._promises.get(promise_id)

    def resolve(self, promise_id: str, result: Any = None) -> bool:
        p = self._promises.get(promise_id)
        if p:
            p.resolve(result)
            return True
        return False

    def reject(self, promise_id: str, error: str) -> bool:
        p = self._promises.get(promise_id)
        if p:
            p.reject(error)
            return True
        return False

    def list_promises(self, state: Optional[PromiseState] = None) -> List[Dict[str, Any]]:
        if state:
            return [p.to_dict() for p in self._promises.values() if p.state == state]
        return [p.to_dict() for p in self._promises.values()]

    def stats(self) -> Dict[str, Any]:
        resolved = sum(1 for p in self._promises.values() if p.state == PromiseState.RESOLVED)
        rejected = sum(1 for p in self._promises.values() if p.state == PromiseState.REJECTED)
        pending = sum(1 for p in self._promises.values() if p.state == PromiseState.PENDING)
        return {"total": len(self._promises), "resolved": resolved,
                "rejected": rejected, "pending": pending}

    def clear_completed(self) -> int:
        to_remove = [k for k, v in self._promises.items() if v.handled()]
        for k in to_remove:
            del self._promises[k]
        return len(to_remove)
