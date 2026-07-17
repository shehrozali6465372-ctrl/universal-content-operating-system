"""Publish Failure Memory — Track publishing failures, recovery, error frequency."""
from __future__ import annotations
from typing import Any, Dict, List


class FailureEntry:
    """A recorded publishing failure."""

    __slots__ = ("platform", "error_type", "error_message",
                 "recovered", "recovery_action", "attempts", "timestamp")

    def __init__(self, platform: str = "", error_type: str = "") -> None:
        self.platform = platform
        self.error_type = error_type
        self.error_message: str = ""
        self.recovered: bool = False
        self.recovery_action: str = ""
        self.attempts: int = 1
        self.timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "error_type": self.error_type,
            "error_message": self.error_message[:100],
            "recovered": self.recovered,
            "recovery_action": self.recovery_action,
            "attempts": self.attempts,
        }


class PublishFailureMemory:
    """Track publishing failures and recovery effectiveness."""

    def __init__(self) -> None:
        self._entries: List[FailureEntry] = []
        self._error_counts: Dict[str, int] = {}
        self._recovery_counts: Dict[str, int] = {}
        self._platform_failures: Dict[str, int] = {}

    def record(self, entry: FailureEntry) -> None:
        self._entries.append(entry)
        self._error_counts[entry.error_type] = self._error_counts.get(entry.error_type, 0) + 1
        self._platform_failures[entry.platform] = self._platform_failures.get(entry.platform, 0) + 1
        if entry.recovered:
            self._recovery_counts[entry.recovery_action] = self._recovery_counts.get(entry.recovery_action, 0) + 1

    def get_error_frequency(self) -> Dict[str, int]:
        return dict(sorted(self._error_counts.items(), key=lambda x: x[1], reverse=True))

    def get_recovery_effectiveness(self) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for action, count in self._recovery_counts.items():
            total = sum(1 for e in self._entries if e.recovery_action == action)
            result[action] = round(count / max(1, total), 3)
        return result

    def get_platform_failures(self) -> Dict[str, int]:
        return dict(sorted(self._platform_failures.items(), key=lambda x: x[1], reverse=True))

    def get_entries(self, platform: str = "", error_type: str = "") -> List[FailureEntry]:
        results = self._entries
        if platform:
            results = [e for e in results if e.platform == platform]
        if error_type:
            results = [e for e in results if e.error_type == error_type]
        return results

    def get_total_failures(self) -> int:
        return len(self._entries)

    def get_recovery_rate(self) -> float:
        if not self._entries:
            return 1.0
        recovered = sum(1 for e in self._entries if e.recovered)
        return round(recovered / len(self._entries), 3)
