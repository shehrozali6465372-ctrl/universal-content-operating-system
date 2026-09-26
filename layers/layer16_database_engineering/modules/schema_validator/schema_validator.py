"""Schema metadata validator with type and constraint checks."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Any,Dict,List,Optional
class ColumnType(str,Enum):
    TEXT="text";INTEGER="integer";FLOAT="float";BOOLEAN="boolean";DATETIME="datetime";JSON="json";BLOB="blob"
@dataclass(frozen=True,slots=True)
class ColumnDef:
    name:str;column_type:ColumnType=ColumnType.TEXT;nullable:bool=True;default:Any=None;primary_key:bool=False;unique:bool=False;indexed:bool=False;max_length:Optional[int]=None
    def to_dict(self)->Dict[str,Any]:return {"name":self.name,"type":self.column_type.value,"nullable":self.nullable,"primary_key":self.primary_key,"unique":self.unique}
class TableSchema:
    def __init__(self,table_name:str,columns:Optional[List[ColumnDef]]=None)->None:
        if not table_name:raise ValueError("table_name is required")
        self.table_name=table_name;self.columns=list(columns or [])
    def add_column(self,column:ColumnDef)->None:
        if any(c.name==column.name for c in self.columns):raise ValueError(f"duplicate column: {column.name}")
        self.columns.append(column)
    def get_column(self,name:str)->Optional[ColumnDef]:return next((c for c in self.columns if c.name==name),None)
def _type_matches(t:ColumnType,v:Any)->bool:
    if t==ColumnType.TEXT:return isinstance(v,str)
    if t==ColumnType.INTEGER:return isinstance(v,int) and not isinstance(v,bool)
    if t==ColumnType.FLOAT:return isinstance(v,(int,float)) and not isinstance(v,bool)
    if t==ColumnType.BOOLEAN:return isinstance(v,bool)
    if t==ColumnType.DATETIME:return hasattr(v,"tzinfo") and hasattr(v,"isoformat")
    if t==ColumnType.JSON:return isinstance(v,(dict,list,str,int,float,bool))
    if t==ColumnType.BLOB:return isinstance(v,(bytes,bytearray,memoryview))
    return False
class SchemaValidator:
    def __init__(self)->None:self._schemas={};self._errors:List[str]=[];self._lock=RLock()
    def register_schema(self,schema:TableSchema)->None:
        with self._lock:
            if schema.table_name in self._schemas:raise ValueError(f"schema already registered: {schema.table_name}")
            self._schemas[schema.table_name]=schema
    def validate(self,table_name:str,data:Dict[str,Any])->Dict[str,Any]:
        with self._lock:
            schema=self._schemas.get(table_name)
            if schema is None:return {"valid":False,"errors":[f"Schema not found: {table_name}"]}
            errors=[];known={c.name for c in schema.columns};errors.extend(f"Unknown column: {n}" for n in sorted(set(data)-known))
            for c in schema.columns:
                if c.name not in data:
                    if not c.nullable and c.default is None:errors.append(f"Missing required column: {c.name}")
                    continue
                v=data[c.name]
                if v is None:
                    if not c.nullable:errors.append(f"Column {c.name} cannot be null")
                    continue
                if not _type_matches(c.column_type,v):errors.append(f"Column {c.name} has invalid type")
                if c.max_length is not None and isinstance(v,str) and len(v)>c.max_length:errors.append(f"Column {c.name} exceeds max length {c.max_length}")
            self._errors.extend(errors);return {"valid":not errors,"errors":errors}
    def validate_batch(self,table_name:str,records:List[Dict[str,Any]])->Dict[str,Any]:
        results=[self.validate(table_name,r) for r in records];invalid=sum(not r["valid"] for r in results)
        return {"total":len(records),"valid":len(records)-invalid,"invalid":invalid}
    def get_errors(self)->List[str]:
        with self._lock:return list(self._errors)
    def list_schemas(self)->List[str]:
        with self._lock:return sorted(self._schemas)
