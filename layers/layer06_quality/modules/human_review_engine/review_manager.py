"""Review Manager — production human review and approval workflow."""
from __future__ import annotations

import time
from threading import RLock
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.human_review_engine.confidence_router import (
    ConfidenceRouter,
)
from layers.layer06_quality.modules.human_review_engine.review_models import (
    AuditEntry,
    ReviewComment,
    ReviewRequest,
    WORKFLOW_STAGES,
)
from layers.layer06_quality.modules.human_review_engine.workflow_manager import (
    WorkflowManager,
)


VALID_RISK_CATEGORIES = frozenset(
    {"normal", "sensitive", "legal", "financial", "medical", "political"}
)


class ReviewManager:
    """Orchestrate review state transitions without duplicate approvals."""

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
        self._lock = RLock()

    def create_request(
        self,
        content: str,
        title: str = "",
        author: str = "",
        confidence_score: float = 0.5,
        risk_category: str = "normal",
    ) -> ReviewRequest:
        """Create a validated review request."""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")
        if not 0.0 <= confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0 and 1")
        if risk_category not in VALID_RISK_CATEGORIES:
            raise ValueError(f"unsupported risk category: {risk_category}")

        with self._lock:
            req = ReviewRequest(
                request_id=self._next_id,
                content=content,
                title=title,
                author=author,
            )
            req.confidence_score = confidence_score
            req.risk_category = risk_category
            req.audit_log.append(
                AuditEntry(
                    action="created",
                    actor=author,
                    to_stage="draft",
                    reason="Review request created",
                )
            )
            self._requests[req.request_id] = req
            self._next_id += 1
            self._check_count += 1
            return req

    def submit_for_review(self, request_id: int, actor: str = "") -> tuple:
        """Submit content from draft to review."""
        with self._lock:
            req = self._requests.get(request_id)
            if not req:
                return False, f"Request {request_id} not found"
            return self.workflow.transition(
                req, "review", actor=actor, reason="Submitted for review"
            )

    def approve(
        self, request_id: int, reviewer: str = "", comment: str = ""
    ) -> tuple:
        """Record one unique reviewer approval and transition when complete."""
        with self._lock:
            req = self._requests.get(request_id)
            if not req:
                return False, f"Request {request_id} not found"
            reviewer = reviewer.strip()
            if not reviewer:
                return False, "reviewer is required"
            if req.current_stage != "review":
                return (
                    False,
                    f"Approval is only allowed during review, not {req.current_stage}",
                )
            if req.current_approvals >= req.required_approvals:
                return False, "Request already has all required approvals"

            approved_by = req.metadata.setdefault("approved_by", [])
            if reviewer in approved_by:
                return False, f"Reviewer {reviewer} has already approved this request"
            if req.assigned_reviewers and reviewer not in req.assigned_reviewers:
                return False, f"Reviewer {reviewer} is not assigned to this request"

            approved_by.append(reviewer)
            req.current_approvals += 1
            req.audit_log.append(
                AuditEntry(
                    action="approved",
                    actor=reviewer,
                    from_stage=req.current_stage,
                    to_stage=req.current_stage,
                    reason=comment or "Approved",
                )
            )

            if req.current_approvals < req.required_approvals:
                req.updated_at = time.time()
                return (
                    True,
                    f"Approval recorded ({req.current_approvals}/"
                    f"{req.required_approvals})",
                )

            ok, message = self.workflow.transition(
                req, "approved", actor=reviewer, reason="All approvals received"
            )
            if not ok:
                approved_by.remove(reviewer)
                req.current_approvals -= 1
                return False, message
            return True, message

    def reject(
        self, request_id: int, reviewer: str = "", reason: str = ""
    ) -> tuple:
        """Reject and reset approval state before returning to draft."""
        with self._lock:
            req = self._requests.get(request_id)
            if not req:
                return False, f"Request {request_id} not found"
            ok, message = self.workflow.transition(
                req, "draft", actor=reviewer, reason=reason or "Rejected"
            )
            if ok:
                req.current_approvals = 0
                req.metadata.pop("approved_by", None)
            return ok, message

    def schedule(self, request_id: int, actor: str = "") -> tuple:
        """Schedule approved content."""
        with self._lock:
            req = self._requests.get(request_id)
            if not req:
                return False, f"Request {request_id} not found"
            return self.workflow.transition(
                req, "scheduled", actor=actor, reason="Scheduled for publishing"
            )

    def publish(self, request_id: int, actor: str = "") -> tuple:
        """Publish scheduled content."""
        with self._lock:
            req = self._requests.get(request_id)
            if not req:
                return False, f"Request {request_id} not found"
            return self.workflow.transition(
                req, "published", actor=actor, reason="Published"
            )

    def add_comment(
        self,
        request_id: int,
        reviewer: str,
        text: str,
        severity: str = "info",
        position_start: int = -1,
        position_end: int = -1,
        category: str = "general",
    ) -> Optional[ReviewComment]:
        """Add a review comment."""
        with self._lock:
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
        with self._lock:
            return self._requests.get(request_id)

    def get_by_stage(self, stage: str) -> List[ReviewRequest]:
        with self._lock:
            return [r for r in self._requests.values() if r.current_stage == stage]

    def get_pending_review(self) -> List[ReviewRequest]:
        return self.get_by_stage("review")

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall review statistics."""
        with self._lock:
            all_reqs = list(self._requests.values())
            return {
                "total_requests": len(all_reqs),
                "by_stage": {
                    stage: len(
                        [r for r in all_reqs if r.current_stage == stage]
                    )
                    for stage in WORKFLOW_STAGES
                },
                "total_comments": sum(len(r.comments) for r in all_reqs),
                "total_audit_entries": sum(
                    len(r.audit_log) for r in all_reqs
                ),
                "avg_confidence": round(
                    sum(r.confidence_score for r in all_reqs)
                    / max(1, len(all_reqs)),
                    3,
                ),
            }

    @property
    def check_count(self) -> int:
        with self._lock:
            return self._check_count
