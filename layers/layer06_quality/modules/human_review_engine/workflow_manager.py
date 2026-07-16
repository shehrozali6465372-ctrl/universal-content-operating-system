"""Workflow Manager — Manages review workflow stage transitions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Tuple

from layers.layer06_quality.modules.human_review_engine.review_models import (
    ReviewRequest, AuditEntry,
)


VALID_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["review"],
    "review": ["approved", "draft"],  # Can be sent back for revision
    "approved": ["scheduled"],
    "scheduled": ["published", "draft"],  # Can be pulled back
    "published": [],
}


class WorkflowManager:
    """Manage workflow stage transitions with validation."""

    def __init__(self) -> None:
        self._transition_count = 0

    def can_transition(self, current_stage: str, target_stage: str) -> bool:
        """Check if a transition is valid."""
        valid = VALID_TRANSITIONS.get(current_stage, [])
        return target_stage in valid

    def transition(
        self, request: ReviewRequest, target_stage: str,
        actor: str = "", reason: str = "",
    ) -> Tuple[bool, str]:
        """Attempt a workflow transition."""
        if not self.can_transition(request.current_stage, target_stage):
            return False, f"Invalid transition: {request.current_stage} → {target_stage}"

        old_stage = request.current_stage
        request.current_stage = target_stage
        request.updated_at = time.time()

        entry = AuditEntry(
            action="transition",
            actor=actor,
            from_stage=old_stage,
            to_stage=target_stage,
            reason=reason,
        )
        request.audit_log.append(entry)
        self._transition_count += 1
        return True, f"Transitioned: {old_stage} → {target_stage}"

    def get_valid_transitions(self, current_stage: str) -> List[str]:
        """Get valid next stages."""
        return VALID_TRANSITIONS.get(current_stage, [])

    def get_stage_history(self, request: ReviewRequest) -> List[Dict[str, Any]]:
        """Get complete stage transition history."""
        return [
            {"from": e.from_stage, "to": e.to_stage, "actor": e.actor, "time": e.timestamp}
            for e in request.audit_log if e.action == "transition"
        ]

    @property
    def transition_count(self) -> int:
        return self._transition_count
