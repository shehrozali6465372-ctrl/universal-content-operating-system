"""transaction_manager.py — Transaction management."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class Transaction:
    """Single database transaction."""
    __slots__ = ("tx_id", "status", "operations", "started_at", "committed_at",
                 "rolled_back", "metadata")
    _counter = 0

    def __init__(self) -> None:
        Transaction._counter += 1
        self.tx_id: int = Transaction._counter
        self.status: str = "active"
        self.operations: List[Dict[str, Any]] = []
        self.started_at: float = time.time()
        self.committed_at: float = 0.0
        self.rolled_back: bool = False
        self.metadata: Dict[str, Any] = {}

    def add_operation(self, op_type: str, sql: str, params: Dict[str, Any] = None) -> None:
        self.operations.append({"type": op_type, "sql": sql, "params": params or {}})

    def to_dict(self) -> Dict[str, Any]:
        return {"tx_id": self.tx_id, "status": self.status,
                "operations": len(self.operations), "started_at": self.started_at}


class TransactionManager:
    """Manages database transactions."""

    def __init__(self) -> None:
        self._transactions: Dict[int, Transaction] = {}
        self._completed: List[Transaction] = []
        self._auto_commit: bool = True

    def begin(self) -> Transaction:
        tx = Transaction()
        self._transactions[tx.tx_id] = tx
        return tx

    def commit(self, tx_id: int) -> bool:
        tx = self._transactions.pop(tx_id, None)
        if tx:
            tx.status = "committed"
            tx.committed_at = time.time()
            self._completed.append(tx)
            return True
        return False

    def rollback(self, tx_id: int) -> bool:
        tx = self._transactions.pop(tx_id, None)
        if tx:
            tx.status = "rolled_back"
            tx.rolled_back = True
            self._completed.append(tx)
            return True
        return False

    def execute_in_transaction(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        tx = self.begin()
        try:
            result = func(*args, **kwargs)
            self.commit(tx.tx_id)
            return result
        except Exception:
            self.rollback(tx.tx_id)
            raise

    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        return self._transactions.get(tx_id)

    def get_active(self) -> List[Transaction]:
        return list(self._transactions.values())

    def get_completed(self) -> List[Transaction]:
        return list(self._completed)

    def stats(self) -> Dict[str, Any]:
        return {"active": len(self._transactions), "completed": len(self._completed),
                "total_created": Transaction._counter}
