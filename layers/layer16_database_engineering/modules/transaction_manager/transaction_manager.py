"""TransactionManager — database transaction coordination."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class TxState(str, Enum):
    ACTIVE = "active"; COMMITTED = "committed"; ROLLED_BACK = "rolled_back"; FAILED = "failed"


class DBTransaction:
    __slots__ = ("tx_id", "state", "operations", "compensations",
                 "created_at", "finished_at", "metadata")

    def __init__(self, tx_id: Optional[str] = None) -> None:
        self.tx_id = tx_id or str(uuid.uuid4())[:12]
        self.state = TxState.ACTIVE
        self.operations: List[Dict[str, Any]] = []
        self.compensations: List[Callable] = []
        self.created_at = time.time()
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"tx_id": self.tx_id, "state": self.state.value,
                "operations": len(self.operations)}


class DBTransactionManager:
    def __init__(self) -> None:
        self._transactions: Dict[str, DBTransaction] = {}
        self._history: List[Dict[str, Any]] = []

    def begin(self, tx_id: Optional[str] = None) -> DBTransaction:
        tx = DBTransaction(tx_id)
        self._transactions[tx.tx_id] = tx
        return tx

    def add_operation(self, tx_id: str, name: str, execute: Callable,
                      compensate: Optional[Callable] = None) -> bool:
        tx = self._transactions.get(tx_id)
        if not tx or tx.state != TxState.ACTIVE:
            return False
        tx.operations.append({"name": name, "execute": execute})
        if compensate:
            tx.compensations.append(compensate)
        return True

    def commit(self, tx_id: str) -> Dict[str, Any]:
        tx = self._transactions.get(tx_id)
        if not tx:
            return {"error": "not_found"}
        results = []
        for op in tx.operations:
            try:
                result = op["execute"]()
                results.append({"name": op["name"], "success": True})
            except Exception as exc:
                for comp in reversed(tx.compensations):
                    try:
                        comp()
                    except Exception:
                        pass
                tx.state = TxState.FAILED
                tx.finished_at = time.time()
                self._history.append(tx.to_dict())
                return {"error": str(exc), "rolled_back": True}
        tx.state = TxState.COMMITTED
        tx.finished_at = time.time()
        self._history.append(tx.to_dict())
        return {"status": "committed", "results": results}

    def rollback(self, tx_id: str) -> Dict[str, Any]:
        tx = self._transactions.get(tx_id)
        if not tx:
            return {"error": "not_found"}
        for comp in reversed(tx.compensations):
            try:
                comp()
            except Exception:
                pass
        tx.state = TxState.ROLLED_BACK
        tx.finished_at = time.time()
        self._history.append(tx.to_dict())
        return {"status": "rolled_back"}

    def get_transaction(self, tx_id: str) -> Optional[DBTransaction]:
        return self._transactions.get(tx_id)

    def list_transactions(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._transactions.values()]
