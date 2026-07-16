"""Review Manager — Core orchestrator for human review and approval."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.human_review_engine.review_models import (
    ReviewRequest, ReviewComment, AuditEntry, WORKFLOW_STAGES,
)
from layers.layer06_quality.modules.human_review_engine.workflow_manager import WorkflowManager
from layers.layer06_quality.modules.human_review_engine.confidence_router import ConfidenceRouter


class ReviewManager:
    """Orchestrates the full review and approval pipeline."""

    def __init__(
        self,
        workflow_manager: Optional[WorkflowManager] = None,
        confidence_router: Optional[ConfidenceRouter] = None,
    ) -> None:
        self.workflow = workflow_manager or WorkflowManager()
        self.router = confidence_router or ConfidenceRouter()
        self._requests: Dict[int, ReviewRequest] = {}
        self._next_id = 1
        self._check_count = 0

    def create_request(
        self,
        content: str,
        title: str = "",
        author: str = "",
        confidence_score: float = 0.5,
        risk_category: str = "normal",
    ) -> ReviewRequest:
        """Create a new review request."""
        req = ReviewRequest(
            request_id=self._next_id,
            content=content,
            title=title,
            author=author,
        )
        req.confidence_score = confidence_score
        req.risk_category = risk_category

        entry = AuditEntry(
            action="created", actor=author,
            to_stage="draft", reason="Review request created",
        )
        req.audit_log.append(entry)

        self._requests[req.request_id] = req
        self._next_id += 1
        self._check_count += 1
        return req

    def submit_for_review(self, request_id: int, actor: str = "") -> tuple:
        """Submit content from draft to review."""
        req = self._requests.get(request_id)
        if not req:
            return False, f"Request {request_id} not found"
        return self.workflow.transition(req, "review", actor=actor, reason="Submitted for review")

    def approve(self, request_id: int, reviewer: str = "", comment: str = "") -> tuple:
        """Approve content."""
        req = self._requests.get(request_id)
        if not req:
            return False, f"Request {request_id} not found"

        req.current_approvals += 1
        entry = AuditEntry(
            action="approved", actor=reviewer,
            from_stage=req.current_stage, to_stage=req.current_stage,
            reason=comment or "Approved",
        )
        req.audit_log.append(entry)

        if req.current_approvals >= req.required_approvals:
            return self.workflow.transition(req, "approved", actor=reviewer, reason="All approvals received")
        return True, f"Approval recorded ({req.current_approvals}/{req.required_approvals})"

    def reject(self, request_id: int, reviewer: str = "", reason: str = "") -> tuple:
        """Reject and send back to draft."""
        req = self._requests.get(request_id)
        if not req:
            return False, f"Request {request_id} not found"
        return self.workflow.transition(req, "draft", actor=reviewer, reason=reason or "Rejected")

    def schedule(self, request_id: int, actor: str = "") -> tuple:
        """Schedule approved content."""
        req = self._requests.get(request_id)
        if not req:
            return False, f"Request {request_id} not found"
        return self.workflow.transition(req, "scheduled", actor=actor, reason="Scheduled for publishing")

    def publish(self, request_id: int, actor: str = "") -> tuple:
        """Publish scheduled content."""
        req = self._requests.get(request_id)
        if not req:
            return False, f"Request {request_id} not found"
        return self.workflow.transition(req, "published", actor=actor, reason="Published")

    def add_comment(
        self, request_id: int, reviewer: str, text: str,
        severity: str = "info", position_start: int = -1,
        position_end: int = -1, category: str = "general",
    ) -> Optional[ReviewComment]:
        """Add a review comment."""
        req = self._requests.get(request_id)
        if not req:
            return None

        comment = ReviewComment(
            comment_id=len(req.comments) + 1,
            reviewer=reviewer,
            text=text,
            severity=severity,
            position_start=position_start,
            position_end=position_end,
            category=category,
        )
        req.comments.append(comment)
        req.updated_at = time.time()
        return comment

    def get_request(self, request_id: int) -> Optional[ReviewRequest]:
        return self._requests.get(request_id)

    def get_by_stage(self, stage: str) -> List[ReviewRequest]:
        return [r for r in self._requests.values() if r.current_stage == stage]

    def get_pending_review(self) -> List[ReviewRequest]:
        return self.get_by_stage("review")

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall review statistics."""
        all_reqs = list(self._requests.values())
        return {
            "total_requests": len(all_reqs),
            "by_stage": {stage: len([r for r in all_reqs if r.current_stage == stage]) for stage in WORKFLOW_STAGES},
            "total_comments": sum(len(r.comments) for r in all_reqs),
            "total_audit_entries": sum(len(r.audit_log) for r in all_reqs),
            "avg_confidence": round(sum(r.confidence_score for r in all_reqs) / max(1, len(all_reqs)), 3),
        }

    @property
    def check_count(self) -> int:
        return self._check_count
