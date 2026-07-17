"""Memory Cleanup — Remove stale, expired, and low-value memory entries."""
from __future__ import annotations
from typing import Any, Dict, List


class CleanupAction:
    """A single cleanup action taken on a memory entry."""

    __slots__ = ("entry_id", "action", "reason", "original_score", "new_score")

    def __init__(self, entry_id: str = "", action: str = "keep") -> None:
        self.entry_id = entry_id
        self.action = action
        self.reason: str = ""
        self.original_score: float = 0.0
        self.new_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "action": self.action,
            "reason": self.reason,
            "original_score": round(self.original_score, 3),
        }


class CleanupReport:
    """Summary of a cleanup operation."""

    __slots__ = ("total_checked", "kept", "archived", "deleted",
                 "actions", "space_freed")

    def __init__(self) -> None:
        self.total_checked: int = 0
        self.kept: int = 0
        self.archived: int = 0
        self.deleted: int = 0
        self.actions: List[CleanupAction] = []
        self.space_freed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_checked": self.total_checked,
            "kept": self.kept,
            "archived": self.archived,
            "deleted": self.deleted,
            "space_freed": self.space_freed,
        }


class MemoryCleanup:
    """Clean up stale, expired, and low-value memory entries."""

    DEFAULT_CONFIG = {
        "max_age_days": 90,
        "min_score": 0.2,
        "min_usage": 1,
        "archive_threshold": 0.3,
        "delete_threshold": 0.1,
    }

    def __init__(self, config: dict = None) -> None:
        self._config = dict(config or self.DEFAULT_CONFIG)
        self._reports: List[CleanupReport] = []

    def cleanup(self, entries: List[Dict[str, Any]]) -> CleanupReport:
        report = CleanupReport()
        report.total_checked = len(entries)
        for entry in entries:
            action = self._evaluate_entry(entry)
            report.actions.append(action)
            if action.action == "archive":
                report.archived += 1
            elif action.action == "delete":
                report.deleted += 1
            else:
                report.kept += 1
        report.space_freed = report.deleted + report.archived
        self._reports.append(report)
        return report

    def _evaluate_entry(self, entry: Dict[str, Any]) -> CleanupAction:
        entry_id = entry.get("entry_id", "unknown")
        action = CleanupAction(entry_id)
        action.original_score = entry.get("score", 0.5)

        score = entry.get("score", 0.5)
        age_days = entry.get("age_days", 0.0)
        usage_count = entry.get("usage_count", 0)

        if score < self._config["delete_threshold"]:
            action.action = "delete"
            action.reason = f"Score {score} below delete threshold"
        elif (age_days > self._config["max_age_days"] and
              usage_count < self._config["min_usage"] and
              score < self._config["archive_threshold"]):
            action.action = "archive"
            action.reason = f"Age {age_days:.0f}d, usage {usage_count}, score {score}"
        elif score < self._config["archive_threshold"]:
            action.action = "archive"
            action.reason = f"Low score {score}"
        else:
            action.action = "keep"
            action.reason = "Entry meets retention criteria"
        return action

    def get_reports(self) -> List[CleanupReport]:
        return list(self._reports)
