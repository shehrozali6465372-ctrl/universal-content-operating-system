"""Integrity-verified backup snapshots; real PostgreSQL backup remains Layer 13."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass,field
from hashlib import sha256
from json import dumps
from threading import RLock
from time import time
from typing import Any,Dict,List,Optional
from uuid import uuid4
def _digest(data:Dict[str,Any])->str:return sha256(dumps(data,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
@dataclass(slots=True)
class BackupEntry:
    name:str
    data:Dict[str,Any]
    backup_id:str=field(default_factory=lambda:uuid4().hex[:12])
    created_at:float=field(default_factory=time)
    @property
    def checksum(self)->str:return _digest(self.data)
    @property
    def size_bytes(self)->int:return len(dumps(self.data,default=str).encode())
    def to_dict(self)->Dict[str,Any]:return {"backup_id":self.backup_id,"name":self.name,"created_at":self.created_at,"size_bytes":self.size_bytes,"checksum":self.checksum}
class BackupManager:
    def __init__(self)->None:self._backups:Dict[str,BackupEntry]={};self._lock=RLock()
    def create_backup(self,name:str,data:Dict[str,Any])->BackupEntry:
        if not name:raise ValueError("backup name is required")
        entry=BackupEntry(name,deepcopy(data))
        with self._lock:self._backups[entry.backup_id]=entry
        return entry
    def restore(self,backup_id:str)->Optional[Dict[str,Any]]:
        with self._lock:
            entry=self._backups.get(backup_id)
            if entry is None:return None
            if _digest(entry.data)!=entry.checksum:raise RuntimeError("backup integrity verification failed")
            return deepcopy(entry.data)
    def verify(self,backup_id:str)->bool:
        with self._lock:
            entry=self._backups.get(backup_id);return entry is not None and _digest(entry.data)==entry.checksum
    def delete_backup(self,backup_id:str)->bool:
        with self._lock:return self._backups.pop(backup_id,None) is not None
    def list_backups(self)->List[Dict[str,Any]]:
        with self._lock:return [b.to_dict() for b in self._backups.values()]
    def count(self)->int:
        with self._lock:return len(self._backups)
