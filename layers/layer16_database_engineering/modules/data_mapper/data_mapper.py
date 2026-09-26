"""Explicit database/domain mapping primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Callable,Dict,List,Optional
Transform=Callable[[Any],Any]
@dataclass(frozen=True,slots=True)
class MappingRule:
    db_field:str;domain_field:str;transform:Optional[Transform]=None;reverse_transform:Optional[Transform]=None
class DataMapper:
    def __init__(self,entity_name:str)->None:
        if not entity_name:raise ValueError("entity_name is required")
        self.entity_name=entity_name;self._rules:List[MappingRule]=[]
    def add_rule(self,db_field:str,domain_field:str,transform:Optional[Transform]=None,reverse_transform:Optional[Transform]=None)->None:
        if not db_field or not domain_field:raise ValueError("mapping fields are required")
        self._rules.append(MappingRule(db_field,domain_field,transform,reverse_transform))
    def to_domain(self,db_record:Dict[str,Any])->Dict[str,Any]:
        result={}
        for rule in self._rules:
            value=db_record.get(rule.db_field)
            result[rule.domain_field]=rule.transform(value) if rule.transform and value is not None else value
        return result
    def to_db(self,domain_obj:Dict[str,Any])->Dict[str,Any]:
        result={}
        for rule in self._rules:
            value=domain_obj.get(rule.domain_field)
            result[rule.db_field]=rule.reverse_transform(value) if rule.reverse_transform and value is not None else value
        return result
    def to_domain_batch(self,records:List[Dict[str,Any]])->List[Dict[str,Any]]:return [self.to_domain(r) for r in records]
    def to_db_batch(self,objects:List[Dict[str,Any]])->List[Dict[str,Any]]:return [self.to_db(o) for o in objects]
    def list_rules(self)->List[Dict[str,Any]]:return [{"db":r.db_field,"domain":r.domain_field} for r in self._rules]
