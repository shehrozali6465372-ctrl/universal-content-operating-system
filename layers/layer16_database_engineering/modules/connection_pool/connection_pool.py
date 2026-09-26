"""Thread-safe bounded connection-handle pool with injectable factory."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from threading import Condition
from time import monotonic
from typing import Any, Callable, Dict, List, Optional

class ConnectionState(str, Enum):
    IDLE="idle"; ACTIVE="active"; CLOSED="closed"; ERROR="error"

@dataclass(slots=True)
class PooledConnection:
    conn_id: str
    config: Dict[str, Any]
    raw_connection: Any = None
    state: ConnectionState = ConnectionState.IDLE
    created_at: float = field(default_factory=monotonic)
    last_used: float = field(default_factory=monotonic)
    use_count: int = 0
    def to_dict(self) -> Dict[str, Any]:
        return {"conn_id": self.conn_id, "state": self.state.value, "use_count": self.use_count}

class ConnectionPool:
    def __init__(self, min_size:int=2, max_size:int=10, db_url:str="",
                 connection_factory:Optional[Callable[[str],Any]]=None) -> None:
        if min_size < 0 or max_size <= 0 or min_size > max_size: raise ValueError("invalid pool bounds")
        self._min_size=min_size; self._max_size=max_size; self._db_url=db_url; self._factory=connection_factory
        self._connections:Dict[str,PooledConnection]={}; self._counter=0; self._closed=False; self._condition=Condition()
    def initialize(self)->int:
        with self._condition:
            if self._closed: raise RuntimeError("pool is closed")
            created=0
            while len(self._connections)<self._min_size: self._create_connection_locked(); created+=1
            return created
    def _create_connection_locked(self)->PooledConnection:
        raw=self._factory(self._db_url) if self._factory else None
        self._counter+=1
        conn=PooledConnection(f"conn_{self._counter}",{"url":self._db_url},raw)
        self._connections[conn.conn_id]=conn; return conn
    def acquire(self,timeout:float=5.0)->Optional[PooledConnection]:
        if timeout<0: raise ValueError("timeout cannot be negative")
        deadline=monotonic()+timeout
        with self._condition:
            if self._closed: raise RuntimeError("pool is closed")
            while True:
                for conn in self._connections.values():
                    if conn.state==ConnectionState.IDLE:
                        conn.state=ConnectionState.ACTIVE; conn.last_used=monotonic(); conn.use_count+=1; return conn
                if len(self._connections)<self._max_size:
                    conn=self._create_connection_locked(); conn.state=ConnectionState.ACTIVE; conn.use_count=1; return conn
                remaining=deadline-monotonic()
                if remaining<=0: return None
                self._condition.wait(timeout=remaining)
    def release(self,conn:PooledConnection)->bool:
        with self._condition:
            current=self._connections.get(conn.conn_id)
            if current is not conn or conn.state!=ConnectionState.ACTIVE: return False
            conn.state=ConnectionState.IDLE; conn.last_used=monotonic(); self._condition.notify(); return True
    def close(self,conn_id:str)->bool:
        with self._condition:
            conn=self._connections.pop(conn_id,None)
            if conn is None: return False
            conn.state=ConnectionState.CLOSED
            if conn.raw_connection is not None and hasattr(conn.raw_connection,"close"): conn.raw_connection.close()
            self._condition.notify_all(); return True
    def close_all(self)->int:
        with self._condition:
            connections=list(self._connections.values()); self._connections.clear()
            for conn in connections:
                conn.state=ConnectionState.CLOSED
                if conn.raw_connection is not None and hasattr(conn.raw_connection,"close"): conn.raw_connection.close()
            self._closed=True; self._condition.notify_all(); return len(connections)
    def stats(self)->Dict[str,Any]:
        with self._condition:
            idle=sum(c.state==ConnectionState.IDLE for c in self._connections.values())
            active=sum(c.state==ConnectionState.ACTIVE for c in self._connections.values())
            return {"total":len(self._connections),"idle":idle,"active":active,"min_size":self._min_size,"max_size":self._max_size}
    def list_connections(self)->List[Dict[str,Any]]:
        with self._condition: return [c.to_dict() for c in self._connections.values()]
