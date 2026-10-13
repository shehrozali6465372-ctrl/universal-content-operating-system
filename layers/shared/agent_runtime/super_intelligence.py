"""Super Intelligence Agent delegation loop with explicit persistence/tool boundaries.

This orchestrator coordinates specialist agents. Production callers must inject a
durable goal store, a planner, and an authorized execution gateway; in-memory
state is deliberately not provided as a fake production implementation.
"""
from __future__ import annotations

from typing import Protocol, Sequence

from .contracts import AgentManifest, AgentResult, AgentRole, AgentRunStatus, AgentScope, AgentTask
from .registry import AgentRegistry


class GoalPlanError(RuntimeError):
    pass


class GoalPlanner(Protocol):
    def plan(self, goal_id: str, instruction: str, scope: AgentScope) -> Sequence[AgentTask]:
        """Return bounded specialist tasks with explicit acceptance criteria."""
        ...


class AgentExecutionGateway(Protocol):
    def execute(self, agent: AgentManifest, task: AgentTask) -> AgentResult:
        """Execute one task using only authorized tools and return evidence."""
        ...


class DurableGoalStore(Protocol):
    """Persistence adapter; implementations must be backed by the canonical DB."""

    def create_goal(self, goal_id: str, instruction: str, scope: AgentScope) -> None: ...
    def task_started(self, task: AgentTask, agent: AgentManifest) -> None: ...
    def task_finished(self, task: AgentTask, result: AgentResult) -> None: ...
    def goal_finished(self, goal_id: str, status: str, summary: str) -> None: ...


class SuperIntelligenceAgent:
    """Plan, delegate, validate, and report; specialist agents do domain work."""

    def __init__(
        self,
        *,
        registry: AgentRegistry,
        planner: GoalPlanner,
        executor: AgentExecutionGateway,
        store: DurableGoalStore,
        role: AgentRole = AgentRole.SUPER_INTELLIGENCE,
    ) -> None:
        self._registry = registry
        self._planner = planner
        self._executor = executor
        self._store = store
        self._role = role

    def run_goal(self, goal_id: str, instruction: str, scope: AgentScope) -> dict:
        if not goal_id.strip() or not instruction.strip():
            raise ValueError("goal_id and instruction are required")
        self._store.create_goal(goal_id, instruction, scope)
        tasks = tuple(self._planner.plan(goal_id, instruction, scope))
        if not tasks:
            self._store.goal_finished(goal_id, "blocked", "Planner produced no executable tasks.")
            return {"goal_id": goal_id, "status": "blocked", "results": [], "errors": ["no tasks planned"]}

        results: list[AgentResult] = []
        errors: list[str] = []
        overall = "completed"
        for task in tasks:
            if task.goal_id != goal_id:
                errors.append("Planner emitted a task for a different goal.")
                overall = "failed"
                break
            if task.scope != scope:
                errors.append("Planner emitted a task outside the authorized goal scope.")
                overall = "blocked"
                break
            manifests = self._registry.find_capability(task.capability)
            if not manifests:
                errors.append("No enabled agent supports capability: " + task.capability)
                overall = "blocked"
                break
            # A task must route to one unambiguous specialist. Ambiguity is not a
            # reason to guess which agent gets access to the task or its account.
            if len(manifests) != 1:
                errors.append("Ambiguous agent capability routing: " + task.capability)
                overall = "blocked"
                break
            manifest = manifests[0]
            self._store.task_started(task, manifest)
            try:
                result = self._executor.execute(manifest, task)
                if result.task_id != task.task_id or result.agent_role != manifest.role:
                    raise GoalPlanError("Agent result identity does not match delegated task.")
                if result.status == AgentRunStatus.COMPLETED and not result.evidence:
                    raise GoalPlanError("Agent marked task completed without evidence.")
                self._store.task_finished(task, result)
                results.append(result)
            except Exception as exc:
                errors.append("Task " + task.task_id + " failed: " + type(exc).__name__ + ": " + str(exc)[:300])
                overall = "partial" if results else "failed"
                break
            if result.status == AgentRunStatus.NEEDS_APPROVAL:
                overall = "needs_approval"
                errors.append("Task requires human approval: " + task.task_id)
                break
            if result.status == AgentRunStatus.BLOCKED:
                overall = "blocked"
                errors.extend(result.errors or ("Task blocked: " + task.task_id,))
                break
            if result.status == AgentRunStatus.FAILED:
                overall = "partial" if results else "failed"
                errors.extend(result.errors or ("Task failed: " + task.task_id,))
                break
            if result.status == AgentRunStatus.PARTIAL:
                overall = "partial"
                errors.extend(result.errors)

        summary = (
            f"{len(results)} of {len(tasks)} planned specialist tasks returned results; "
            f"{len(errors)} blocker/error entries."
        )
        self._store.goal_finished(goal_id, overall, summary)
        return {
            "goal_id": goal_id,
            "status": overall,
            "planned_tasks": len(tasks),
            "finished_tasks": len(results),
            "results": [
                {
                    "task_id": result.task_id,
                    "agent_role": result.agent_role.value,
                    "status": result.status.value,
                    "summary": result.summary,
                    "confidence": result.confidence,
                    "evidence": [
                        {"kind": evidence.kind, "reference": evidence.reference, "confidence": evidence.confidence}
                        for evidence in result.evidence
                    ],
                    "errors": list(result.errors),
                    "artifacts": list(result.artifacts),
                }
                for result in results
            ],
            "errors": errors,
            "summary": summary,
        }
