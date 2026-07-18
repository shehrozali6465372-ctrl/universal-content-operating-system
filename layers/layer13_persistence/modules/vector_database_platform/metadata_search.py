"""metadata_search.py — Metadata-based filtering."""
from __future__ import annotations
from typing import Any, Dict, List


class MetadataSearch:
    """Filters vectors by metadata attributes."""

    def __init__(self) -> None:
        self._operators = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            "in": lambda a, b: a in b,
            "nin": lambda a, b: a not in b,
            "contains": lambda a, b: b in str(a),
        }

    def filter(self, records: List[Dict[str, Any]],
               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for record in records:
            meta = record.get("metadata", {})
            if self._matches(meta, filters):
                results.append(record)
        return results

    def _matches(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, condition in filters.items():
            if isinstance(condition, dict):
                for op, value in condition.items():
                    meta_val = metadata.get(key)
                    if meta_val is None:
                        return False
                    op_func = self._operators.get(op)
                    if op_func and not op_func(meta_val, value):
                        return False
            else:
                if metadata.get(key) != condition:
                    return False
        return True
