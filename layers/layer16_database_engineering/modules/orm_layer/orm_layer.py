"""Thread-safe model metadata/store used only as an engineering primitive.

Layer 13 remains the production persistence owner; this class never pretends to be a database.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from time import time
from typing import Any,ClassVar,Dict,List,Optional
@dataclass(frozen=True,slots=True)
class Field:
    name:str;field_type:str="str";default:Any=None;nullable:bool=True;primary_key:bool=False;unique:bool=False;indexed:bool=False;max_length:Optional[int]=None
class ModelMeta:
    def __init__(self,table_name:str,fields:List[Field])->None:
        if not table_name or not fields:raise ValueError("table_name and fields are required")
        names=[f.name for f in fields]
        if len(names)!=len(set(names)):raise ValueError("duplicate field names")
        if sum(f.primary_key for f in fields)>1:raise ValueError("multiple primary keys are not supported")
        self.table_name=table_name;self.fields=list(fields);self.primary_key=next((f.name for f in fields if f.primary_key),"id")
    def to_dict(self)->Dict[str,Any]:
        return {"table_name":self.table_name,"fields":[{"name":f.name,"type":f.field_type,"nullable":f.nullable,"primary_key":f.primary_key} for f in self.fields]}
class BaseModel:
    _meta:ClassVar[Optional[ModelMeta]]=None;_store:ClassVar[Dict[str,Dict[str,Any]]]={};_store_lock:ClassVar[RLock]=RLock()
    def __init__(self,**kwargs:Any)->None:
        if self._meta is None:raise RuntimeError("model metadata is not configured")
        for field in self._meta.fields:
            value=kwargs.get(field.name,field.default)
            if value is None and not field.nullable:raise ValueError(f"Field {field.name} cannot be null")
            if field.max_length is not None and isinstance(value,str) and len(value)>field.max_length:raise ValueError(f"Field {field.name} exceeds max length")
            setattr(self,field.name,value)
    def save(self)->Dict[str,Any]:
        assert self._meta is not None
        data={f.name:getattr(self,f.name,None) for f in self._meta.fields};pk=data.get(self._meta.primary_key)
        if pk is None:raise ValueError(f"primary key {self._meta.primary_key} is required")
        data["_saved_at"]=time()
        with self._store_lock:self.__class__._store[str(pk)]=deepcopy(data);return deepcopy(data)
    @classmethod
    def get_by_id(cls,pk:str)->Optional[Dict[str,Any]]:
        with cls._store_lock:
            value=cls._store.get(str(pk));return deepcopy(value) if value is not None else None
    @classmethod
    def all(cls)->List[Dict[str,Any]]:
        with cls._store_lock:return deepcopy(list(cls._store.values()))
    @classmethod
    def filter_by(cls,**kwargs:Any)->List[Dict[str,Any]]:
        with cls._store_lock:return deepcopy([r for r in cls._store.values() if all(r.get(k)==v for k,v in kwargs.items())])
    @classmethod
    def delete(cls,pk:str)->bool:
        with cls._store_lock:return cls._store.pop(str(pk),None) is not None
    @classmethod
    def count(cls)->int:
        with cls._store_lock:return len(cls._store)
    @classmethod
    def clear(cls)->int:
        with cls._store_lock:count=len(cls._store);cls._store.clear();return count
    def to_dict(self)->Dict[str,Any]:
        assert self._meta is not None
        return {f.name:getattr(self,f.name,None) for f in self._meta.fields}
