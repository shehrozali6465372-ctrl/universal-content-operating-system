"""Thread-safe transaction coordinator with correct compensation semantics."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from time import time
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

class TxState(str,Enum):
    ACTIVE="active"; COMMITTED="committed"; ROLLED_BACK="rolled_back"; FAILED="failed"

@dataclass(slots=True)
class DBTransaction:
    tx_id:str=field(default_factory=lambda:uuid4().hex[:12])
    state:TxState=TxState.ACTIVE
    operations:List[Dict[str,Any]]=field(default_factory=list)
    created_at:float=field(default_factory=time)
    finished_at:float=0.0
    def to_dict(self)->Dict[str,Any]:
        return {"tx_id":self.tx_id,"state":self.state.value,"operations":len(self.operations),
                "created_at":self.created_at,"finished_at":self.finished_at}

class DBTransactionManager:
    def __init__(self)->None: self._transactions={}; self._history=[]; self._lock=RLock()
    def begin(self,tx_id:Optional[str]=None)->DBTransaction:
        with self._lock:
            tx=DBTransaction(tx_id=tx_id or uuid4().hex[:12])
            if tx.tx_id in self._transactions: raise ValueError(f"transaction already exists: {tx.tx_id}")
            self._transactions[tx.tx_id]=tx; return tx
    def add_operation(self,tx_id:str,name:str,execute:Callable[[],Any],compensate:Optional[Callable[[],Any]]=None)->bool:
        if not name or not callable(execute): raise ValueError("name and execute callable are required")
        with self._lock:
            tx=self._transactions.get(tx_id)
            if tx is None or tx.state!=TxState.ACTIVE: return False
            tx.operations.append({"name":name,"execute":execute,"compensate":compensate}); return True
    def commit(self,tx_id:str)->Dict[str,Any]:
        with self._lock:
            tx=self._transactions.get(tx_id)
            if tx is None: return {"error":"not_found"}
            if tx.state!=TxState.ACTIVE: return {"error":"invalid_state","state":tx.state.value}
            executed=[]; results=[]
            for op in tx.operations:
                try:
                    result=op["execute"](); results.append({"name":op["name"],"success":True,"result":result})
                    if op.get("compensate"): executed.append(op["compensate"])
                except Exception as exc:
                    compensation_errors=[]
                    for comp in reversed(executed):
                        try: comp()
                        except Exception as comp_exc: compensation_errors.append(str(comp_exc))
                    tx.state=TxState.FAILED; tx.finished_at=time(); self._history.append(tx.to_dict())
                    return {"error":str(exc),"rolled_back":True,"compensation_errors":compensation_errors}
            tx.state=TxState.COMMITTED; tx.finished_at=time(); self._history.append(tx.to_dict())
            return {"status":"committed","results":results}
    def rollback(self,tx_id:str)->Dict[str,Any]:
        with self._lock:
            tx=self._transactions.get(tx_id)
            if tx is None: return {"error":"not_found"}
            if tx.state!=TxState.ACTIVE: return {"error":"invalid_state","state":tx.state.value}
            tx.state=TxState.ROLLED_BACK; tx.finished_at=time(); self._history.append(tx.to_dict()); return {"status":"rolled_back"}
    def get_transaction(self,tx_id:str)->Optional[DBTransaction]:
        with self._lock: return self._transactions.get(tx_id)
    def list_transactions(self)->List[Dict[str,Any]]:
        with self._lock: return [t.to_dict() for t in self._transactions.values()]
