"""Review Models — Data models for the review and approval workflow."""
from __future__ import annotations
import time
from typing import Any, Dict, List


WORKFLOW_STAGES = ("draft", "review", "approved", "scheduled", "published")
RISK_CATEGORIES = ("normal", "sensitive", "legal", "financial", "medical", "political")


class ReviewComment:
    """A single review comment with location."""

    __slots__ = ("comment_id", "reviewer", "text", "severity",
                 "position_start", "position_end", "category",
                 "created_at", "resolved")

    def __init__(
        self,
        comment_id: int = 0,
        reviewer: str = "",
        text: str = "",
        severity: str = "info",
        position_start: int = -1,
        position_end: int = -1,
        category: str = "general",
    ) -> None:
        self.comment_id = comment_id
        self.reviewer = reviewer
        self.text = text
        self.severity = severity  # info, suggestion, warning, critical
        self.position_start = position_start
        self.position_end = position_end
        self.category = category
        self.created_at = time.time()
        self.resolved = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "reviewer": self.reviewer,
            "text": self.text,
            "severity": self.severity,
            "position_start": self.position_start,
            "position_end": self.position_end,
            "category": self.category,
            "created_at": self.created_at,
            "resolved": self.resolved,
        }


class AuditEntry:
    """An audit log entry."""

    __slots__ = ("action", "actor", "timestamp", "from_stage",
                 "to_stage", "reason", "metadata")

    def __init__(
        self,
        action: str = "",
        actor: str = "",
        from_stage: str = "",
        to_stage: str = "",
        reason: str = "",
    ) -> None:
        self.action = action
        self.actor = actor
        self.timestamp = time.time()
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.reason = reason
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "reason": self.reason,
            "metadata": self.metadata,
        }


class ReviewRequest:
    """A review request for content."""

    __slots__ = (
        "request_id", "content", "title", "current_stage",
        "confidence_score", "risk_category", "author",
        "assigned_reviewers", "required_approvals",
        "current_approvals", "comments", "audit_log",
        "created_at", "updated_at", "metadata",
    )

    def __init__(
        self,
        request_id: int = 0,
        content: str = "",
        title: str = "",
        author: str = "",
    ) -> None:
        self.request_id = request_id
        self.content = content
        self.title = title
        self.current_stage = "draft"
        self.confidence_score = 0.5
        self.risk_category = "normal"
        self.author = author
        self.assigned_reviewers: List[str] = []
        self.required_approvals = 1
        self.current_approvals = 0
        self.comments: List[ReviewComment] = []
        self.audit_log: List[AuditEntry] = []
        self.created_at = time.time()
        self.updated_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "title": self.title,
            "current_stage": self.current_stage,
            "confidence_score": self.confidence_score,
            "risk_category": self.risk_category,
            "author": self.author,
            "assigned_reviewers": self.assigned_reviewers,
            "required_approvals": self.required_approvals,
            "current_approvals": self.current_approvals,
            "comment_count": len(self.comments),
            "audit_entries": len(self.audit_log),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
