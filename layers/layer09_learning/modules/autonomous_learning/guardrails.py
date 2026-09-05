"""Deployment decisions are evidence-gated and fail closed."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .policy import PolicyRecord, PolicyRegistry
from .scope import LearningScope


@dataclass(frozen=True)
class GuardrailConfig:
    min_observations: int = 100
    min_relative_improvement: float = 0.02
    max_error_regression: float = 0.0
    canary_min_observations: int = 50


@dataclass(frozen=True)
class DeploymentDecision:
    action: str
    scope_key: str
    reason: str
    evidence_count: int
    baseline_metric: Optional[float] = None
    candidate_metric: Optional[float] = None
    relative_improvement: Optional[float] = None


class DeploymentGuard:
    def __init__(self, registry: PolicyRegistry, config: GuardrailConfig | None = None) -> None:
        self.registry = registry
        self.config = config or GuardrailConfig()

    def qualify_candidate(self, scope: LearningScope, *, candidate_metric: float, baseline_metric: float | None, evidence_count: int) -> DeploymentDecision:
        if evidence_count < self.config.min_observations:
            return DeploymentDecision("insufficient_evidence", scope.key, "minimum evidence not met", evidence_count, baseline_metric, candidate_metric)
        if baseline_metric is None:
            return DeploymentDecision("promote", scope.key, "first validated candidate with sufficient evidence", evidence_count, None, candidate_metric, None)
        if baseline_metric == 0:
            improvement = None
            acceptable = candidate_metric <= self.config.max_error_regression
        else:
            improvement = (baseline_metric - candidate_metric) / abs(baseline_metric)
            acceptable = candidate_metric <= baseline_metric * (1.0 + self.config.max_error_regression) and improvement >= self.config.min_relative_improvement
        return DeploymentDecision("promote" if acceptable else "reject", scope.key,
                                  "candidate meets measured guardrails" if acceptable else "candidate failed measured guardrails",
                                  evidence_count, baseline_metric, candidate_metric, improvement)

    def start_canary(self, scope: LearningScope, policy_id: str, version: int, *, evidence_id: str, evidence_count: int) -> DeploymentDecision:
        if evidence_count < self.config.canary_min_observations:
            return DeploymentDecision("insufficient_evidence", scope.key, "canary evidence threshold not met", evidence_count)
        self.registry.transition(scope, policy_id, version, "canary", evidence_id=evidence_id)
        return DeploymentDecision("canary", scope.key, "candidate entered canary", evidence_count)

    def promote(self, scope: LearningScope, policy_id: str, version: int, *, evidence_id: str, evidence_count: int) -> DeploymentDecision:
        if evidence_count < self.config.min_observations:
            return DeploymentDecision("insufficient_evidence", scope.key, "promotion evidence threshold not met", evidence_count)
        self.registry.transition(scope, policy_id, version, "active", evidence_id=evidence_id)
        return DeploymentDecision("promote", scope.key, "policy promoted from verified canary", evidence_count)

    def rollback(self, scope: LearningScope, policy_id: str, version: int, *, reason: str) -> DeploymentDecision:
        self.registry.transition(scope, policy_id, version, "rolled_back", rollback_reason=reason)
        safe = self.registry.get_safe_rollback(scope, exclude_version=version)
        if safe is None:
            return DeploymentDecision("no_safe_rollback", scope.key, "no previously retired policy exists in exact scope", 0)
        return DeploymentDecision("rollback", scope.key, f"rollback target is {safe.policy_id}@{safe.version}", 0)
