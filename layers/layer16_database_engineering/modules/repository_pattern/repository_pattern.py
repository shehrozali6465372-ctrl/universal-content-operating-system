"""Thread-safe repository abstraction with consistent secondary indexes."""
from __future__ import annotations
from copy import deepcopy
from threading import RLock
from time import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

class BaseRepository:
    def __init__(self,entity_name:str)->None:
        if not entity_name: raise ValueError("entity_name is required")
        self.entity_name=entity_name; self._store={}; self._index={}; self._lock=RLock()
    def _generate_id(self)->str: return f"{self.entity_name}_{uuid4().hex[:8]}"
    def add(self,data:Dict[str,Any],entity_id:Optional[str]=None)->Dict[str,Any]:
        with self._lock:
            eid=entity_id or self._generate_id()
            if eid in self._store: raise ValueError(f"entity already exists: {eid}")
            now=time(); record={"id":eid,**deepcopy(data),"_created_at":now,"_updated_at":now}
            self._store[eid]=record; self._rebuild_indexes_locked(); return deepcopy(record)
    def get(self,entity_id:str)->Optional[Dict[str,Any]]:
        with self._lock:
            record=self._store.get(entity_id); return deepcopy(record) if record else None
    def update(self,entity_id:str,data:Dict[str,Any])->Optional[Dict[str,Any]]:
        with self._lock:
            record=self._store.get(entity_id)
            if record is None: return None
            record.update(deepcopy(data)); record["_updated_at"]=time(); self._rebuild_indexes_locked(); return deepcopy(record)
    def delete(self,entity_id:str)->bool:
        with self._lock:
            if self._store.pop(entity_id,None) is None: return False
            self._rebuild_indexes_locked(); return True
    def list_all(self)->List[Dict[str,Any]]:
        with self._lock: return deepcopy(list(self._store.values()))
    def find_by(self,field:str,value:Any)->List[Dict[str,Any]]:
        with self._lock: return deepcopy([r for r in self._store.values() if r.get(field)==value])
    def find_one_by(self,field:str,value:Any)->Optional[Dict[str,Any]]:
        rows=self.find_by(field,value); return rows[0] if rows else None
    def count(self)->int:
        with self._lock: return len(self._store)
    def exists(self,entity_id:str)->bool:
        with self._lock: return entity_id in self._store
    def create_index(self,field:str)->None:
        if not field: raise ValueError("index field is required")
        with self._lock: self._index[field]={}; self._rebuild_indexes_locked()
    def _rebuild_indexes_locked(self)->None:
        for field in list(self._index):
            index={}
            for eid,record in self._store.items(): index.setdefault(str(record.get(field,"")),set()).add(eid)
            self._index[field]=index
    def find_by_index(self,index_name:str,value:Any)->List[Dict[str,Any]]:
        with self._lock:
            ids=self._index.get(index_name,{}).get(str(value),set())
            return deepcopy([self._store[eid] for eid in ids if eid in self._store])
    def clear(self)->int:
        with self._lock:
            count=len(self._store); self._store.clear(); self._rebuild_indexes_locked(); return count
    def bulk_add(self,items:List[Dict[str,Any]])->List[Dict[str,Any]]: return [self.add(item) for item in items]
