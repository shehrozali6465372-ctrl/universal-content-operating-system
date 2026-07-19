"""AIDiffEngine — compare AI outputs and detect changes."""
from __future__ import annotations
from typing import Any, Dict, List

class AIDiffEngine:
    def __init__(self) -> None:
        self._diffs: List[Dict[str, Any]] = []
    def compare(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        changes: List[str] = []
        all_keys = set(list(before.keys()) + list(after.keys()))
        for k in all_keys:
            if before.get(k) != after.get(k):
                changes.append(k)
        result = {"changed_keys": changes, "total_changes": len(changes),
                  "unchanged": len(all_keys) - len(changes)}
        self._diffs.append(result); return result
    def get_history(self) -> List[Dict[str, Any]]: return list(self._diffs)
