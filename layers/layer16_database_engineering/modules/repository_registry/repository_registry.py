"""Thread-safe repository registry."""
from __future__ import annotations
from threading import RLock
from typing import Any,Dict,List,Optional
class RepositoryRegistry:
    def __init__(self)->None:self._repositories:Dict[str,Any]={};self._lock=RLock()
    def register(self,name:str,repository:Any,*,replace:bool=False)->None:
        if not name:raise ValueError("repository name is required")
        with self._lock:
            if name in self._repositories and not replace:raise ValueError(f"repository already registered: {name}")
            self._repositories[name]=repository
    def unregister(self,name:str)->bool:
        with self._lock:return self._repositories.pop(name,None) is not None
    def get(self,name:str)->Optional[Any]:
        with self._lock:return self._repositories.get(name)
    def has(self,name:str)->bool:
        with self._lock:return name in self._repositories
    def list_repositories(self)->List[str]:
        with self._lock:return sorted(self._repositories)
    def count(self)->int:
        with self._lock:return len(self._repositories)
