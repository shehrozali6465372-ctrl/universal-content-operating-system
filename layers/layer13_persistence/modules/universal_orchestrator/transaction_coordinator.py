"""transaction_coordinator.py — Distributed transaction coordination."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DistributedTransaction:
    """A distributed transaction."""
    __slots__ = ("tx_id", "operations", "status", "started_at", "completed_at")
    _counter = 0

    def __init__(self) -> None:
        DistributedTransaction._counter += 1
        self.tx_id: int = DistributedTransaction._counter
        self.operations: List[Dict[str, Any]] = []
        self.status: str = "active"
        self.started_at: float = time.time()
        self.completed_at: float = 0.0


class TransactionCoordinator:
    """Coordinates transactions across multiple stores."""

    def __init__(self) -> None:
        self._transactions: Dict[int, DistributedTransaction] = {}
        self._completed: List[DistributedTransaction] = []

    def begin(self) -> DistributedTransaction:
        tx = DistributedTransaction()
        self._transactions[tx.tx_id] = tx
        return tx

    def add_operation(self, tx_id: int, store: str, op: str, data: Any) -> bool:
        tx = self._transactions.get(tx_id)
        if tx:
            tx.operations.append({"store": store, "op": op, "data": data})
            return True
        return False

    def commit(self, tx_id: int) -> bool:
        tx = self._transactions.pop(tx_id, None)
        if tx:
            tx.status = "committed"
            tx.completed_at = time.time()
            self._completed.append(tx)
            return True
        return False

    def rollback(self, tx_id: int) -> bool:
        tx = self._transactions.pop(tx_id, None)
        if tx:
            tx.status = "rolled_back"
            self._completed.append(tx)
            return True
        return False

    def get_active(self) -> List[DistributedTransaction]:
        return list(self._transactions.values())

    def stats(self) -> Dict[str, Any]:
        return {"active": len(self._transactions), "completed": len(self._completed)}
