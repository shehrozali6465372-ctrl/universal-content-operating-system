"""Recovery Actions — Concrete recovery steps for each failure type."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional

from layers.layer07_publishing.modules.failure_recovery.failure_detector import FailureRecord
from layers.layer07_publishing.modules.failure_recovery.error_classifier import ErrorClassification


class RecoveryAction:
    """A single recovery action to execute."""

    __slots__ = ("action_type", "description", "priority", "executable", "requires_confirmation")

    ACTION_TYPES = (
        "refresh_token", "re_upload_media", "switch_endpoint", "delay_publish",
        "retry_immediate", "retry_exponential", "force_resync",
        "notify_admin", "skip_and_continue", "abort",
    )

    def __init__(
        self,
        action_type: str = "",
        description: str = "",
        executable: Optional[Callable[[], bool]] = None,
        requires_confirmation: bool = False,
    ) -> None:
        self.action_type = action_type if action_type in self.ACTION_TYPES else "retry_immediate"
        self.description = description
        self.executable = executable
        self.priority: int = 5
        self.requires_confirmation = requires_confirmation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "priority": self.priority,
            "requires_confirmation": self.requires_confirmation,
        }

    def execute(self) -> bool:
        if self.executable:
            try:
                return self.executable()
            except Exception:
                return False
        return True


class RecoveryActions:
    """Factory for creating recovery actions based on failure type."""

    @staticmethod
    def suggest_actions(
        record: FailureRecord,
        classification: ErrorClassification,
    ) -> List[RecoveryAction]:
        actions: List[RecoveryAction] = []

        if classification.category == "retryable":
            if record.error_type == "rate_limit":
                actions.append(RecoveryAction("retry_exponential", "Wait and retry with backoff"))
                actions.append(RecoveryAction("delay_publish", "Delay and retry"))
            elif record.error_type == "network":
                actions.append(RecoveryAction("retry_immediate", "Immediate retry"))
                actions.append(RecoveryAction("switch_endpoint", "Switch API endpoint"))
            else:
                actions.append(RecoveryAction("retry_exponential", "Exponential backoff retry"))

        elif classification.category == "permanent":
            if record.error_type == "auth":
                actions.append(RecoveryAction("refresh_token", "Refresh auth token",
                                              requires_confirmation=False))
                actions.append(RecoveryAction("notify_admin", "Notify admin of auth failure",
                                              requires_confirmation=True))
            elif record.error_type == "content":
                actions.append(RecoveryAction("skip_and_continue", "Skip and continue"))
                actions.append(RecoveryAction("abort", "Abort publishing", requires_confirmation=True))

        elif classification.category == "platform_specific":
            actions.append(RecoveryAction("force_resync", "Resync platform state"))
            actions.append(RecoveryAction("notify_admin", "Notify admin", requires_confirmation=True))

        else:
            actions.append(RecoveryAction("retry_immediate", "Immediate retry"))
            actions.append(RecoveryAction("notify_admin", "Manual review required",
                                          requires_confirmation=True))

        for i, a in enumerate(actions):
            a.priority = i + 1
        return actions

    @staticmethod
    def get_recommended_action(
        record: FailureRecord,
        classification: ErrorClassification,
    ) -> RecoveryAction:
        actions = RecoveryActions.suggest_actions(record, classification)
        return actions[0] if actions else RecoveryAction("skip_and_continue", "Skip")
