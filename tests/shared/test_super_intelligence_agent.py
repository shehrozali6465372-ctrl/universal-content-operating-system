from layers.shared.agent_runtime import (
    AgentEvidence, AgentManifest, AgentRegistry, AgentRole, AgentRunStatus,
    AgentScope, AgentTask, AgentResult, SuperIntelligenceAgent,
)


class Planner:
    def __init__(self, tasks):
        self.tasks = tasks

    def plan(self, goal_id, instruction, scope):
        return self.tasks


class Store:
    def __init__(self):
        self.events = []

    def create_goal(self, goal_id, instruction, scope):
        self.events.append(("goal_created", goal_id))

    def task_started(self, task, agent):
        self.events.append(("task_started", task.task_id, agent.role))

    def task_finished(self, task, result):
        self.events.append(("task_finished", task.task_id, result.status))

    def goal_finished(self, goal_id, status, summary):
        self.events.append(("goal_finished", goal_id, status))


class Executor:
    def __init__(self, status=AgentRunStatus.COMPLETED):
        self.calls = []
        self.status = status

    def execute(self, agent, task):
        self.calls.append((agent, task))
        return AgentResult(
            task_id=task.task_id,
            agent_role=agent.role,
            status=self.status,
            summary="Research evidence returned",
            evidence=(AgentEvidence(kind="source_url", reference="https://example.com/research"),),
            confidence=0.9,
        )


def setup_agent(task):
    registry = AgentRegistry()
    registry.register(AgentManifest(role=AgentRole.RESEARCH, capabilities=("research:products",), version="1.0"))
    store = Store()
    executor = Executor()
    agent = SuperIntelligenceAgent(
        registry=registry, planner=Planner([task]), executor=executor, store=store,
    )
    return agent, executor, store


def test_super_intelligence_delegates_explicit_task_and_persists_outcome():
    scope = AgentScope("tenant-1", "workspace-1", "brand-1")
    task = AgentTask(
        goal_id="goal-1", instruction="Research skincare candidates and cite sources",
        capability="research:products", scope=scope,
        acceptance_criteria=("return source URLs", "list recurring complaints"),
    )
    agent, executor, store = setup_agent(task)

    report = agent.run_goal("goal-1", "Find skincare products and compare reviews", scope)

    assert report["status"] == "completed"
    assert report["finished_tasks"] == 1
    assert executor.calls[0][1].instruction.startswith("Research skincare")
    assert store.events[-1] == ("goal_finished", "goal-1", "completed")
    assert report["results"][0]["evidence"][0]["reference"] == "https://example.com/research"


def test_super_intelligence_blocks_task_outside_goal_scope():
    scope = AgentScope("tenant-1", "workspace-1", "brand-1")
    wrong_scope = AgentScope("tenant-2", "workspace-1", "brand-1")
    task = AgentTask(
        goal_id="goal-1", instruction="Research products", capability="research:products",
        scope=wrong_scope,
    )
    agent, executor, store = setup_agent(task)

    report = agent.run_goal("goal-1", "Research products", scope)

    assert report["status"] == "blocked"
    assert not executor.calls
    assert "outside the authorized goal scope" in report["errors"][0]


def test_super_intelligence_blocks_when_no_agent_has_capability():
    scope = AgentScope("tenant-1", "workspace-1", "brand-1")
    task = AgentTask(goal_id="goal-1", instruction="Generate image", capability="image:generate", scope=scope)
    agent, executor, store = setup_agent(task)

    report = agent.run_goal("goal-1", "Create a product image", scope)

    assert report["status"] == "blocked"
    assert not executor.calls
    assert "No enabled agent supports capability" in report["errors"][0]
