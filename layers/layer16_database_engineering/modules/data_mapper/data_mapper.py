"""DataMapper — map between database records and domain objects."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional


class MappingRule:
    __slots__ = ("db_field", "domain_field", "transform", "reverse_transform")

    def __init__(self, db_field: str, domain_field: str,
                 transform: Optional[Callable] = None,
                 reverse_transform: Optional[Callable] = None) -> None:
        self.db_field = db_field
        self.domain_field = domain_field
        self.transform = transform
        self.reverse_transform = reverse_transform


class DataMapper:
    def __init__(self, entity_name: str) -> None:
        self.entity_name = entity_name
        self._rules: List[MappingRule] = []

    def add_rule(self, db_field: str, domain_field: str,
                 transform: Optional[Callable] = None,
                 reverse_transform: Optional[Callable] = None) -> None:
        self._rules.append(MappingRule(db_field, domain_field, transform, reverse_transform))

    def to_domain(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for rule in self._rules:
            val = db_record.get(rule.db_field)
            if rule.transform and val is not None:
                val = rule.transform(val)
            result[rule.domain_field] = val
        return result

    def to_db(self, domain_obj: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for rule in self._rules:
            val = domain_obj.get(rule.domain_field)
            if rule.reverse_transform and val is not None:
                val = rule.reverse_transform(val)
            result[rule.db_field] = val
        return result

    def to_domain_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.to_domain(r) for r in records]

    def to_db_batch(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.to_db(o) for o in objects]

    def list_rules(self) -> List[Dict[str, Any]]:
        return [{"db": r.db_field, "domain": r.domain_field} for r in self._rules]
