"""MemoryValidator — validate memory entries and queries."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import MemoryEntry, MemoryQuery


class MemoryValidator:
    """Validate memory entries and queries."""

    def __init__(self) -> None:
        self._validation_errors: List[Dict[str, Any]] = []

    def validate_entry(self, entry: MemoryEntry) -> Dict[str, Any]:
        issues: List[str] = []
        warnings: List[str] = []

        if not entry.content or not entry.content.strip():
            issues.append("Empty content")
        if entry.importance < 0 or entry.importance > 1.0:
            issues.append(f"Invalid importance: {entry.importance}")
        if entry.confidence < 0 or entry.confidence > 1.0:
            issues.append(f"Invalid confidence: {entry.confidence}")
        if len(entry.content) > 10000:
            warnings.append("Very long content")
        if entry.importance > 0.9:
            warnings.append("Very high importance — verify accuracy")

        valid = len(issues) == 0
        if not valid:
            self._validation_errors.append({"entry_id": entry.entry_id, "issues": issues})
        return {"valid": valid, "issues": issues, "warnings": warnings}

    def validate_query(self, query: MemoryQuery) -> Dict[str, Any]:
        issues: List[str] = []
        if not query.query_text and not query.tags:
            issues.append("Empty query — provide text or tags")
        if query.limit < 1 or query.limit > 1000:
            issues.append(f"Invalid limit: {query.limit}")
        return {"valid": len(issues) == 0, "issues": issues}

    def get_errors(self) -> List[Dict[str, Any]]:
        return list(self._validation_errors)
