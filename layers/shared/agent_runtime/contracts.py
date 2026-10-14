"""Stable contracts for UCOS goal-driven specialist agents.

This module defines transport-neutral contracts only. Durable persistence,
authorization, scheduling, and provider integrations belong to their existing
runtime/service boundaries and must be wired explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class AgentRunStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    NEEDS_APPROVAL = "needs_approval"


class AgentRole(str, Enum):
    SUPER_INTELLIGENCE = "super_intelligence"
    RESEARCH = "research"
    TEXT = "text"
    IMAGE_INTELLIGENCE = "image_intelligence"
    PRODUCT_AFFILIATE = "product_affiliate"
    QUALITY = "quality"
    SECURITY = "security"
    PUBLISH_YOUTUBE = "publish_youtube"
    PUBLISH_FACEBOOK = "publish_facebook"
    PUBLISH_TIKTOK = "publish_tiktok"
    PUBLISH_INSTAGRAM = "publish_instagram"
    PUBLISH_PINTEREST = "publish_pinterest"


@dataclass(frozen=True)
class AgentScope:
    """Authorization and memory isolation boundary for an agent run."""

    tenant_id: str
    workspace_id: str
    brand_id: str
    platform_account_ref: str | None = None

    def __post_init__(self) -> None:
        for name in ("tenant_id", "workspace_id", "brand_id"):
            if not getattr(self, name).strip():
                raise ValueError(name + " is required")
        if self.platform_account_ref is not None and not self.platform_account_ref.strip():
            raise ValueError("platform_account_ref must be omitted or non-empty")


@dataclass(frozen=True)
class AgentTask:
    """A bounded delegation instruction from the Super Intelligence Agent."""

    goal_id: str
    instruction: str
    capability: str
    scope: AgentScope
    input_data: Mapping[str, Any] = field(default_factory=dict)
    acceptance_criteria: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    prohibited_actions: tuple[str, ...] = ()
    deadline_at: str | None = None
    max_attempts: int = 3
    budget_usd: float | None = None
    task_id: str = field(default_factory=lambda: "task_" + uuid4().hex)
    parent_task_id: str | None = None
    correlation_id: str = field(default_factory=lambda: uuid4().hex)
    idempotency_key: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        for name in ("goal_id", "instruction", "capability"):
            if not getattr(self, name).strip():
                raise ValueError(name + " is required")
        if self.max_attempts < 1 or self.max_attempts > 10:
            raise ValueError("max_attempts must be between 1 and 10")
        if self.budget_usd is not None and self.budget_usd < 0:
            raise ValueError("budget_usd cannot be negative")


@dataclass(frozen=True)
class AgentEvidence:
    kind: str
    reference: str
    description: str = ""
    confidence: float | None = None
    observed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.kind.strip() or not self.reference.strip():
            raise ValueError("evidence kind and reference are required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    agent_role: AgentRole
    status: AgentRunStatus
    summary: str
    output: Mapping[str, Any] = field(default_factory=dict)
    evidence: tuple[AgentEvidence, ...] = ()
    confidence: float = 0.0
    errors: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.summary.strip():
            raise ValueError("task_id and summary are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status == AgentRunStatus.COMPLETED and self.errors:
            raise ValueError("completed results cannot contain unresolved errors")
        if self.status == AgentRunStatus.COMPLETED and not self.evidence:
            raise ValueError("completed results require evidence")
        if self.status == AgentRunStatus.BLOCKED and not self.errors:
            raise ValueError("blocked results must explain the blocker")


@dataclass(frozen=True)
class AgentManifest:
    role: AgentRole
    capabilities: tuple[str, ...]
    version: str
    platform: str | None = None
    required_tools: tuple[str, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("agent version is required")
        if not self.capabilities or any(not c.strip() for c in self.capabilities):
            raise ValueError("at least one non-empty capability is required")
        if self.role.name.startswith("PUBLISH_") and not self.platform:
            raise ValueError("platform publisher agents require a platform identifier")
