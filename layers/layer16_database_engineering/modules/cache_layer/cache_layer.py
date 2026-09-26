"""Thread-safe bounded LRU cache with monotonic TTL."""
from __future__ import annotations
from dataclasses import dataclass,field
from threading import RLock
from time import monotonic
from typing import Any,Dict,List,Optional
@dataclass(slots=True)
class CacheEntry:
    key:str;value:Any;ttl:Optional[float]
    created_at:float=field(default_factory=monotonic)
    last_access:float=field(default_factory=monotonic)
    access_count:int=0
    def is_expired(self)->bool:return self.ttl is not None and monotonic()-self.created_at>=self.ttl
    def to_dict(self)->Dict[str,Any]:return {"key":self.key,"access_count":self.access_count,"expired":self.is_expired()}
class CacheLayer:
    def __init__(self,max_size:int=1000)->None:
        if max_size<=0:raise ValueError("max_size must be positive")
        self._cache:Dict[str,CacheEntry]={};self._max_size=max_size;self._hits=0;self._misses=0;self._lock=RLock()
    def get(self,key:str)->Any:
        with self._lock:
            e=self._cache.get(key)
            if e is None or e.is_expired():
                self._misses+=1
                if e is not None:del self._cache[key]
                return None
            e.access_count+=1;e.last_access=monotonic();self._hits+=1;return e.value
    def set(self,key:str,value:Any,ttl:Optional[float]=None)->None:
        if ttl is not None and ttl<0:raise ValueError("ttl cannot be negative")
        with self._lock:
            if key not in self._cache and len(self._cache)>=self._max_size:self._evict_lru()
            self._cache[key]=CacheEntry(key,value,ttl)
    def has(self,key:str)->bool:
        with self._lock:return key in self._cache and not self._cache[key].is_expired()
    def delete(self,key:str)->bool:
        with self._lock:return self._cache.pop(key,None) is not None
    def clear(self)->int:
        with self._lock:count=len(self._cache);self._cache.clear();return count
    def cleanup_expired(self)->int:
        with self._lock:
            keys=[k for k,e in self._cache.items() if e.is_expired()]
            for k in keys:del self._cache[k]
            return len(keys)
    def _evict_lru(self)->None:del self._cache[min(self._cache,key=lambda k:self._cache[k].last_access)]
    def keys(self)->List[str]:
        with self._lock:return [k for k,e in self._cache.items() if not e.is_expired()]
    def size(self)->int:
        with self._lock:return len(self._cache)
    def stats(self)->Dict[str,Any]:
        with self._lock:
            total=self._hits+self._misses
            return {"size":len(self._cache),"max_size":self._max_size,"hits":self._hits,"misses":self._misses,"hit_rate":round(self._hits/max(total,1),3)}
