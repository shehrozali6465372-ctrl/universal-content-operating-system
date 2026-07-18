"""storage_cleaner.py — Storage cleanup."""
from __future__ import annotations
from typing import Any, Dict, List


class StorageCleaner:
    """Cleans up storage based on rules."""

    def __init__(self) -> None:
        self._rules: List[Dict[str, Any]] = []
        self._cleanup_count: int = 0

    def add_rule(self, name: str, max_age_days: int = 90,
                 pattern: str = "*") -> None:
        self._rules.append({"name": name, "max_age_days": max_age_days,
                             "pattern": pattern})

    def clean(self, objects: List[Dict[str, Any]]) -> int:
        import time
        now = time.time()
        removed = 0
        for obj in objects:
            age_days = (now - obj.get("created_at", now)) / 86400
            for rule in self._rules:
                if age_days > rule["max_age_days"]:
                    removed += 1
                    break
        self._cleanup_count += removed
        return removed

    def get_rules(self) -> List[Dict[str, Any]]:
        return list(self._rules)

    def stats(self) -> Dict[str, Any]:
        return {"rules": len(self._rules), "total_cleaned": self._cleanup_count}
