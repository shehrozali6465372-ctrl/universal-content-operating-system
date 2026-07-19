"""TransactionManager — coordinate atomic operations across layers."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class TxStatus(str, Enum):
    PENDING = "pending"; ACTIVE = "active"; COMMITTING = "committing"
    COMMITTED = "committed"; ROLLING_BACK = "rolling_back"; ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class Transaction:
    __slots__ = ("tx_id", "status", "operations", "compensations",
                 "created_at", "finished_at", "metadata")

    def __init__(self, tx_id: Optional[str] = None) -> None:
        self.tx_id = tx_id or str(uuid.uuid4())[:12]
        self.status = TxStatus.PENDING
        self.operations: List[Dict[str, Any]] = []
        self.compensations: List[Callable] = []
        self.created_at = time.time()
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"tx_id": self.tx_id, "status": self.status.value,
                "operations": len(self.operations), "created_at": self.created_at}


class TransactionManager:
    def __init__(self) -> None:
        self._transactions: Dict[str, Transaction] = {}
        self._history: List[Dict[str, Any]] = []

    def begin(self, tx_id: Optional[str] = None) -> Transaction:
        tx = Transaction(tx_id)
        tx.status = TxStatus.ACTIVE
        self._transactions[tx.tx_id] = tx
        return tx

    def add_operation(self, tx_id: str, name: str, execute: Callable,
                      compensate: Optional[Callable] = None) -> bool:
        tx = self._transactions.get(tx_id)
        if not tx or tx.status != TxStatus.ACTIVE:
            return False
        tx.operations.append({"name": name, "execute": execute})
        if compensate:
            tx.compensations.append(compensate)
        return True

    def commit(self, tx_id: str) -> Dict[str, Any]:
        tx = self._transactions.get(tx_id)
        if not tx:
            return {"error": "transaction_not_found"}
        tx.status = TxStatus.COMMITTING
        results = []
        for op in tx.operations:
            try:
                result = op["execute"]()
                results.append({"name": op["name"], "success": True, "result": str(result)[:100]})
            except Exception as exc:
                tx.status = TxStatus.ROLLING_BACK
                self._rollback(tx)
                tx.status = TxStatus.ROLLED_BACK
                tx.finished_at = time.time()
                self._history.append(tx.to_dict())
                return {"error": str(exc), "rolled_back": True, "results": results}
        tx.status = TxStatus.COMMITTED
        tx.finished_at = time.time()
        self._history.append(tx.to_dict())
        return {"status": "committed", "tx_id": tx_id, "results": results}

    def _rollback(self, tx: Transaction) -> None:
        for comp in reversed(tx.compensations):
            try:
                comp()
            except Exception:
                pass

    def rollback(self, tx_id: str) -> Dict[str, Any]:
        tx = self._transactions.get(tx_id)
        if not tx:
            return {"error": "transaction_not_found"}
        tx.status = TxStatus.ROLLING_BACK
        self._rollback(tx)
        tx.status = TxStatus.ROLLED_BACK
        tx.finished_at = time.time()
        self._history.append(tx.to_dict())
        return {"status": "rolled_back", "tx_id": tx_id}

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        return self._transactions.get(tx_id)

    def list_transactions(self) -> List[Dict[str, Any]]:
        return [tx.to_dict() for tx in self._transactions.values()]

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
