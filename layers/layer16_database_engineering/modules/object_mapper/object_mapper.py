"""Explicit object mapping registry."""
from __future__ import annotations
from dataclasses import dataclass,field
from threading import RLock
from typing import Any,Callable,Dict,List,Optional
@dataclass(slots=True)
class ObjectMapping:
    source_type:str;target_type:str;mappings:Dict[str,str]=field(default_factory=dict);transforms:Dict[str,Callable[[Any],Any]]=field(default_factory=dict)
    def map_field(self,source_field:str,target_field:str,transform:Optional[Callable[[Any],Any]]=None)->None:
        if not source_field or not target_field:raise ValueError("mapping fields are required")
        self.mappings[source_field]=target_field
        if transform:self.transforms[target_field]=transform
class ObjectMapper:
    def __init__(self)->None:self._mappings={};self._lock=RLock()
    def register(self,source_type:str,target_type:str)->ObjectMapping:
        if not source_type or not target_type:raise ValueError("mapping types are required")
        key=f"{source_type}->{target_type}"
        with self._lock:
            if key in self._mappings:raise ValueError(f"mapping already registered: {key}")
            mapping=ObjectMapping(source_type,target_type);self._mappings[key]=mapping;return mapping
    def map_object(self,source_type:str,target_type:str,source:Dict[str,Any])->Dict[str,Any]:
        key=f"{source_type}->{target_type}"
        with self._lock:
            mapping=self._mappings.get(key)
            if mapping is None:raise KeyError(f"mapping not registered: {key}")
            result={}
            for src,tgt in mapping.mappings.items():
                value=source.get(src);transform=mapping.transforms.get(tgt);result[tgt]=transform(value) if transform else value
            return result
    def map_batch(self,source_type:str,target_type:str,sources:List[Dict[str,Any]])->List[Dict[str,Any]]:return [self.map_object(source_type,target_type,s) for s in sources]
    def list_mappings(self)->List[str]:
        with self._lock:return list(self._mappings)
