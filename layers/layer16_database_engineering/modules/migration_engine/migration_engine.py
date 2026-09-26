"""Deterministic migration orchestration with locking and failure visibility."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from time import monotonic
from typing import Any,Callable,Dict,List,Optional
class MigrationStatus(str,Enum):
    PENDING="pending";RUNNING="running";APPLIED="applied";FAILED="failed";ROLLED_BACK="rolled_back"
@dataclass(slots=True)
class Migration:
    version:str;name:str;up_fn:Callable[[],Any];down_fn:Optional[Callable[[],Any]]=None
    status:MigrationStatus=MigrationStatus.PENDING;applied_at:float=0.0;duration_ms:float=0.0
    def to_dict(self)->Dict[str,Any]:return {"version":self.version,"name":self.name,"status":self.status.value,"applied_at":self.applied_at,"duration_ms":self.duration_ms}
class MigrationEngine:
    def __init__(self)->None:self._migrations:Dict[str,Migration]={};self._history=[];self._lock=RLock()
    def add_migration(self,version:str,name:str,up_fn:Callable[[],Any],down_fn:Optional[Callable[[],Any]]=None)->Migration:
        if not version or not name or not callable(up_fn):raise ValueError("version, name and callable up_fn are required")
        with self._lock:
            if version in self._migrations:raise ValueError(f"duplicate migration version: {version}")
            m=Migration(version,name,up_fn,down_fn);self._migrations[version]=m;return m
    def migrate_up(self,target_version:Optional[str]=None)->Dict[str,Any]:
        with self._lock:
            applied=[]
            for version in sorted(self._migrations):
                m=self._migrations[version]
                if m.status==MigrationStatus.APPLIED:continue
                if target_version is not None and version>target_version:break
                m.status=MigrationStatus.RUNNING;started=monotonic()
                try:m.up_fn()
                except Exception as exc:
                    m.status=MigrationStatus.FAILED;self._history.append({"version":version,"status":"failed","error":str(exc)})
                    return {"applied":applied,"failed":m.to_dict(),"error":str(exc)}
                m.status=MigrationStatus.APPLIED;m.applied_at=monotonic();m.duration_ms=(monotonic()-started)*1000;applied.append(m.to_dict())
            return {"applied":applied,"total":len(applied)}
    def migrate_down(self,version:str)->Dict[str,Any]:
        with self._lock:
            rolled=[]
            for current in sorted(self._migrations,reverse=True):
                if current<version:break
                m=self._migrations[current]
                if m.status!=MigrationStatus.APPLIED:continue
                if m.down_fn is None:return {"error":f"No down migration for {current}","rolled_back":rolled}
                try:m.down_fn()
                except Exception as exc:
                    m.status=MigrationStatus.FAILED;return {"error":str(exc),"rolled_back":rolled}
                m.status=MigrationStatus.ROLLED_BACK;rolled.append(m.to_dict())
            return {"rolled_back":rolled}
    def current_version(self)->Optional[str]:
        with self._lock:
            versions=[v for v,m in self._migrations.items() if m.status==MigrationStatus.APPLIED]
            return max(versions) if versions else None
    def pending(self)->List[Dict[str,Any]]:
        with self._lock:return [m.to_dict() for m in self._migrations.values() if m.status==MigrationStatus.PENDING]
    def applied(self)->List[Dict[str,Any]]:
        with self._lock:return [m.to_dict() for m in self._migrations.values() if m.status==MigrationStatus.APPLIED]
    def list_migrations(self)->List[Dict[str,Any]]:
        with self._lock:return [m.to_dict() for m in self._migrations.values()]
