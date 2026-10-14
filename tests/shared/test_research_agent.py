from __future__ import annotations

from typing import Callable

import pytest

from layers.layer02_research.modules.research_orchestrator.workflow_engine import DEFAULT_RESEARCH_PIPELINE
from layers.shared.agent_runtime import (
    AgentManifest, AgentRegistry, AgentResult, AgentRole, AgentRunStatus,
    AgentScope, AgentTask, ResearchAgent, SuperIntelligenceAgent,
)

MODULE_NAMES = tuple(name for name, _dependencies in DEFAULT_RESEARCH_PIPELINE)


def source_backed_module(name: str, *, source_url: str | None = None) -> Callable:
    url = source_url or f"https://research.example/{name}"

    def run(**context):
        return {
            "module": name,
            "topic": context["topic"],
            "niche": context["niche"],
            "findings": [{"claim": f"Finding from {name}", "confidence": 0.85}],
            "sources": [{"url": url, "title": f"Source for {name}"}],
            "confidence": 0.85,
        }

    return run


def module_bindings(**overrides):
    functions = {name: source_backed_module(name) for name in MODULE_NAMES}
    functions.update(overrides)
    return functions


def sample_scope() -> AgentScope:
    return AgentScope(tenant_id="tenant-1", workspace_id="workspace-1", brand_id="brand-1")


def sample_task(**input_data) -> AgentTask:
    return AgentTask(
        goal_id="goal-research-1",
        instruction="Research a topic and return source-backed findings",
        capability="research:topic",
        scope=sample_scope(),
        input_data={"topic": "sensitive skin towels", "niche": "skincare", **input_data},
        acceptance_criteria=("return findings", "cite source URLs"),
    )


def test_research_agent_requires_exact_layer02_workflow_bindings():
    with pytest.raises(ValueError, match="missing Layer 02 modules"):
        ResearchAgent({"trend_discovery": source_backed_module("trend_discovery")})
    extra = module_bindings()
    extra["unused_research_module"] = source_backed_module("unused")
    with pytest.raises(ValueError, match="unused module bindings"):
        ResearchAgent(extra)


def test_research_agent_manifest_declares_one_role_and_bounded_capabilities():
    agent = ResearchAgent(module_bindings())
    manifest = agent.manifest()
    assert manifest.role == AgentRole.RESEARCH
    assert "research:topic" in manifest.capabilities
    assert "layer02.research_pipeline" in manifest.required_tools
    assert manifest.version == "1.0.0"


def test_research_agent_runs_layer02_and_returns_source_evidence():
    agent = ResearchAgent(module_bindings())
    result = agent.execute(agent.manifest(), sample_task())

    assert isinstance(result, AgentResult)
    assert result.status == AgentRunStatus.COMPLETED
    assert result.agent_role == AgentRole.RESEARCH
    assert result.confidence == pytest.approx(0.85)
    assert len(result.output["completed_modules"]) == len(MODULE_NAMES)
    assert len(result.output["source_urls"]) == len(MODULE_NAMES)
    assert result.output["research_plan"]["topic"] == "sensitive skin towels"
    assert {item.kind for item in result.evidence} == {"source_url", "layer02_execution_trace"}


def test_research_agent_does_not_claim_completion_without_source_urls():
    agent = ResearchAgent({
        name: (lambda **context: {"module": name, "findings": ["unsourced"], "confidence": 0.7})
        for name in MODULE_NAMES
    })
    result = agent.execute(agent.manifest(), sample_task())
    assert result.status == AgentRunStatus.PARTIAL
    assert result.output["source_urls"] == []
    assert any("no verifiable HTTP(S) source URLs" in error for error in result.errors)


def test_research_agent_surfaces_module_failure_instead_of_fabricating_success():
    def fail_verification(**_context):
        raise RuntimeError("source validator unavailable")
    agent = ResearchAgent(module_bindings(fact_verification=fail_verification))
    result = agent.execute(agent.manifest(), sample_task())
    assert result.status == AgentRunStatus.PARTIAL
    assert "fact_verification" in result.output["failed_modules"]
    assert any("source validator unavailable" in error for error in result.errors)


def test_task_input_cannot_override_ceo_authorization_scope():
    observed = []

    def inspect_scope(**context):
        observed.append(context)
        return {"module": "scope-check", "sources": [{"url": "https://research.example/scope"}], "confidence": 0.6}

    agent = ResearchAgent(module_bindings(trend_discovery=inspect_scope))
    task = sample_task(tenant_id="tenant-attacker", workspace_id="workspace-attacker", brand_id="brand-attacker")
    result = agent.execute(agent.manifest(), task)
    assert result.status == AgentRunStatus.COMPLETED
    assert observed[0]["tenant_id"] == "tenant-1"
    assert observed[0]["workspace_id"] == "workspace-1"
    assert observed[0]["brand_id"] == "brand-1"


class OneTaskPlanner:
    def __init__(self, task):
        self.task = task

    def plan(self, goal_id, instruction, scope):
        return [self.task]


class DurableStore:
    def __init__(self):
        self.events = []

    def create_goal(self, goal_id, instruction, scope):
        self.events.append(("goal", goal_id))

    def task_started(self, task, agent):
        self.events.append(("started", task.task_id, agent.role))

    def task_finished(self, task, result):
        self.events.append(("finished", task.task_id, result.status))

    def goal_finished(self, goal_id, status, summary):
        self.events.append(("goal_finished", goal_id, status))


def test_ceo_delegates_to_research_agent_and_persists_verified_result():
    research_agent = ResearchAgent(module_bindings())
    task = sample_task()
    registry = AgentRegistry()
    registry.register(research_agent.manifest())
    store = DurableStore()
    ceo = SuperIntelligenceAgent(
        registry=registry, planner=OneTaskPlanner(task),
        executor=research_agent, store=store,
    )
    report = ceo.run_goal(task.goal_id, "Research sensitive skin towels", sample_scope())
    assert report["status"] == "completed"
    assert report["finished_tasks"] == 1
    assert report["results"][0]["agent_role"] == "research"
    assert any(event[0] == "finished" for event in store.events)
    assert store.events[-1] == ("goal_finished", task.goal_id, "completed")


def test_agent_blocks_mismatched_role_and_invalid_topic():
    agent = ResearchAgent(module_bindings())
    publisher_manifest = AgentManifest(
        role=AgentRole.PUBLISH_PINTEREST,
        capabilities=("publish:pinterest",), version="1.0", platform="pinterest",
    )
    assert agent.execute(publisher_manifest, sample_task()).status == AgentRunStatus.BLOCKED

    empty_topic = AgentTask(
        goal_id="goal-2", instruction="Research topic",
        capability="research:topic", scope=sample_scope(),
        input_data={"topic": "   ", "niche": "skincare"},
    )
    assert agent.execute(agent.manifest(), empty_topic).status == AgentRunStatus.BLOCKED
