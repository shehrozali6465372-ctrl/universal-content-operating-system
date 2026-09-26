"""Database index metadata registry with strict identifiers."""
from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from re import fullmatch
from time import time
from typing import Any,Dict,List,Optional
_IDENT=r"[A-Za-z_][A-Za-z0-9_]*"
def _identifier(value:str)->str:
    if not isinstance(value,str) or not fullmatch(_IDENT,value):raise ValueError(f"unsafe SQL identifier: {value!r}")
    return value
class IndexType(str,Enum):HASH="hash";BTREE="btree";GIN="gin";GIST="gist"
@dataclass(slots=True)
class IndexInfo:
    index_name:str;table_name:str;columns:List[str];index_type:IndexType=IndexType.BTREE;unique:bool=False;created_at:float=field(default_factory=time)
    def to_dict(self)->Dict[str,Any]:return {"index_name":self.index_name,"table_name":self.table_name,"columns":list(self.columns),"type":self.index_type.value,"unique":self.unique,"created_at":self.created_at}
class IndexManager:
    def __init__(self)->None:self._indexes:Dict[str,IndexInfo]={}
    def create_index(self,index_name:str,table_name:str,columns:List[str],index_type:IndexType=IndexType.BTREE,unique:bool=False)->IndexInfo:
        _identifier(index_name);_identifier(table_name)
        if not columns:raise ValueError("at least one index column is required")
        normalized=[_identifier(c) for c in columns]
        if index_name in self._indexes:raise ValueError(f"index already exists: {index_name}")
        info=IndexInfo(index_name,table_name,normalized,index_type,unique);self._indexes[index_name]=info;return info
    def drop_index(self,index_name:str)->bool:return self._indexes.pop(index_name,None) is not None
    def get_index(self,index_name:str)->Optional[IndexInfo]:return self._indexes.get(index_name)
    def list_indexes(self,table_name:Optional[str]=None)->List[Dict[str,Any]]:
        if table_name:_identifier(table_name)
        return [i.to_dict() for i in self._indexes.values() if table_name is None or i.table_name==table_name]
    def count(self)->int:return len(self._indexes)
