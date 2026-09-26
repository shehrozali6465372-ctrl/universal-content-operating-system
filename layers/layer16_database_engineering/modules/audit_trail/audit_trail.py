"""Thread-safe bounded audit trail."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass,field
from enum import Enum
from threading import RLock
from time import time
from typing import Any,Dict,List,Optional
from uuid import uuid4
class AuditAction(str,Enum):
    CREATE="create"; READ="read"; UPDATE="update"; DELETE="delete"
@dataclass(slots=True)
class AuditEntry:
    action:AuditAction
    table_name:str
    entity_id:str
    user_id:str="system"
    entry_id:str=field(default_factory=lambda:uuid4().hex[:12])
    timestamp:float=field(default_factory=time)
    old_data:Optional[Dict[str,Any]]=None
    new_data:Optional[Dict[str,Any]]=None
    metadata:Dict[str,Any]=field(default_factory=dict)
    def to_dict(self)->Dict[str,Any]:
        return {"entry_id":self.entry_id,"action":self.action.value,"table_name":self.table_name,
                "entity_id":self.entity_id,"user_id":self.user_id,"timestamp":self.timestamp,
                "old_data":deepcopy(self.old_data),"new_data":deepcopy(self.new_data),"metadata":deepcopy(self.metadata)}
class AuditTrail:
    def __init__(self,max_entries:int=10000)->None:
        if max_entries<=0:raise ValueError("max_entries must be positive")
        self._entries:List[AuditEntry]=[];self._max_entries=max_entries;self._lock=RLock()
    def log(self,action:AuditAction,table_name:str,entity_id:str,old_data:Optional[Dict[str,Any]]=None,
            new_data:Optional[Dict[str,Any]]=None,user_id:str="system")->AuditEntry:
        if not table_name or not entity_id:raise ValueError("table_name and entity_id are required")
        entry=AuditEntry(action,table_name,entity_id,user_id,old_data=deepcopy(old_data),new_data=deepcopy(new_data))
        with self._lock:
            self._entries.append(entry)
            if len(self._entries)>self._max_entries:del self._entries[:-self._max_entries]
        return entry
    def query(self,table_name:Optional[str]=None,action:Optional[AuditAction]=None,entity_id:Optional[str]=None,limit:int=100)->List[Dict[str,Any]]:
        if limit<=0:return []
        with self._lock:entries=list(self._entries)
        if table_name:entries=[e for e in entries if e.table_name==table_name]
        if action:entries=[e for e in entries if e.action==action]
        if entity_id:entries=[e for e in entries if e.entity_id==entity_id]
        return [e.to_dict() for e in entries[-limit:]]
    def count(self)->int:
        with self._lock:return len(self._entries)
    def clear(self)->int:
        with self._lock:count=len(self._entries);self._entries.clear();return count
