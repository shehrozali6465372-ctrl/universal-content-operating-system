"""Memory Optimize — Optimize memory storage and retrieval performance."""
from __future__ import annotations
from typing import Any, Dict, List


class OptimizationAction:
    """A single optimization action."""

    __slots__ = ("action_type", "description", "entries_affected", "impact")

    def __init__(self, action_type: str = "compact") -> None:
        self.action_type = action_type
        self.description: str = ""
        self.entries_affected: int = 0
        self.impact: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "entries_affected": self.entries_affected,
            "impact": self.impact,
        }


class OptimizationReport:
    """Summary of optimization operations."""

    __slots__ = ("total_actions", "space_saved", "actions", "before_count", "after_count")

    def __init__(self) -> None:
        self.total_actions: int = 0
        self.space_saved: int = 0
        self.actions: List[OptimizationAction] = []
        self.before_count: int = 0
        self.after_count: int = 0

    @property
    def reduction_pct(self) -> float:
        if self.before_count == 0:
            return 0.0
        return round((self.space_saved / self.before_count) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_actions": self.total_actions,
            "space_saved": self.space_saved,
            "before_count": self.before_count,
            "after_count": self.after_count,
            "reduction_pct": self.reduction_pct,
        }


class MemoryOptimizer:
    """Optimize memory by compacting, deduplicating, and reorganizing."""

    def __init__(self) -> None:
        self._reports: List[OptimizationReport] = []

    def optimize(self, entries: List[Dict[str, Any]]) -> OptimizationReport:
        report = OptimizationReport()
        report.before_count = len(entries)
        actions = []
        actions.extend(self._remove_duplicates(entries))
        actions.extend(self._compact_empty(entries))
        actions.extend(self._merge_similar(entries))
        report.actions = actions
        report.total_actions = len(actions)
        report.space_saved = sum(a.entries_affected for a in actions)
        report.after_count = max(0, report.before_count - report.space_saved)
        self._reports.append(report)
        return report

    def _remove_duplicates(self, entries: List[Dict[str, Any]]) -> List[OptimizationAction]:
        seen = set()
        dupes = 0
        for e in entries:
            key = e.get("description", "") + str(e.get("tags", []))
            if key in seen:
                dupes += 1
            seen.add(key)
        if dupes > 0:
            action = OptimizationAction("deduplicate")
            action.description = f"Found {dupes} duplicate entries"
            action.entries_affected = dupes
            action.impact = "medium"
            return [action]
        return []

    def _compact_empty(self, entries: List[Dict[str, Any]]) -> List[OptimizationAction]:
        empty = sum(1 for e in entries if not e.get("description", "").strip())
        if empty > 0:
            action = OptimizationAction("compact")
            action.description = f"Found {empty} empty entries"
            action.entries_affected = empty
            action.impact = "low"
            return [action]
        return []

    def _merge_similar(self, entries: List[Dict[str, Any]]) -> List[OptimizationAction]:
        similar = 0
        for i, e1 in enumerate(entries):
            for e2 in entries[i + 1:]:
                t1 = set(e1.get("tags", []))
                t2 = set(e2.get("tags", []))
                if t1 and t2 and len(t1 & t2) > len(t1) * 0.8:
                    similar += 1
        if similar > 0:
            action = OptimizationAction("merge_similar")
            action.description = f"Found {similar} potentially similar entries"
            action.entries_affected = similar
            action.impact = "medium"
            return [action]
        return []

    def get_reports(self) -> List[OptimizationReport]:
        return list(self._reports)
