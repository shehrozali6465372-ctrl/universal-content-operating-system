import pytest

from layers.shared.agent_runtime import (
    AgentEvidence, AgentManifest, AgentRegistry, AgentRegistryError,
    AgentResult, AgentRole, AgentRunStatus, AgentScope, AgentTask,
)


def sample_scope(account=None):
    return AgentScope(tenant_id="tenant-1", workspace_id="workspace-1", brand_id="brand-1", platform_account_ref=account)


def test_task_requires_scope_and_bounded_retry_policy():
    with pytest.raises(ValueError):
        AgentScope(tenant_id="", workspace_id="w", brand_id="b")
    with pytest.raises(ValueError):
        AgentTask(goal_id="g", instruction="research", capability="research", scope=sample_scope(), max_attempts=11)


def test_completed_agent_result_requires_evidence():
    with pytest.raises(ValueError, match="require evidence"):
        AgentResult(task_id="task-1", agent_role=AgentRole.RESEARCH, status=AgentRunStatus.COMPLETED, summary="done")


def test_blocked_result_requires_reason():
    with pytest.raises(ValueError, match="explain the blocker"):
        AgentResult(task_id="task-1", agent_role=AgentRole.SECURITY, status=AgentRunStatus.BLOCKED, summary="blocked")


def test_publisher_is_selected_by_platform_not_account_identity():
    registry = AgentRegistry()
    registry.register(AgentManifest(role=AgentRole.PUBLISH_YOUTUBE, capabilities=("publish:youtube",), version="1.0", platform="youtube"))
    task = AgentTask(goal_id="g", instruction="publish approved video", capability="publish:youtube", scope=sample_scope("youtube-channel-abc"))
    publisher = registry.publisher_for("YouTube", task)
    assert publisher.role == AgentRole.PUBLISH_YOUTUBE
    assert publisher.platform == "youtube"


def test_publisher_requires_explicit_platform_account():
    registry = AgentRegistry()
    registry.register(AgentManifest(role=AgentRole.PUBLISH_PINTEREST, capabilities=("publish:pinterest",), version="1.0", platform="pinterest"))
    task = AgentTask(goal_id="g", instruction="publish approved pin", capability="publish:pinterest", scope=sample_scope())
    with pytest.raises(AgentRegistryError, match="explicitly selected platform account"):
        registry.publisher_for("pinterest", task)


def test_duplicate_publishers_for_same_platform_are_rejected():
    registry = AgentRegistry()
    registry.register(AgentManifest(role=AgentRole.PUBLISH_FACEBOOK, capabilities=("publish:facebook",), version="1.0", platform="facebook"))
    with pytest.raises(AgentRegistryError, match="already registered"):
        registry.register(AgentManifest(role=AgentRole.PUBLISH_INSTAGRAM, capabilities=("publish:instagram",), version="1.0", platform="facebook"))


def test_evidence_confidence_is_bounded():
    with pytest.raises(ValueError):
        AgentEvidence(kind="url", reference="https://example.com", confidence=1.1)
