"""Research specialist backed by the existing UCOS Layer 02 pipeline.

Layer 02 remains the owner of research capabilities. This adapter does not copy
or reimplement those modules. A concrete callable must be bound for every
canonical workflow step; missing or unused bindings fail closed.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlparse

from layers.layer02_research.modules.research_orchestrator import OrchestratorManager
from layers.layer02_research.modules.research_orchestrator.workflow_engine import DEFAULT_RESEARCH_PIPELINE
from layers.layer02_research.modules.research_planner import PlannerManager
from .contracts import AgentEvidence, AgentManifest, AgentResult, AgentRole, AgentRunStatus, AgentTask

RESEARCH_AGENT_VERSION = "1.0.0"
RESEARCH_CAPABILITIES = (
    "research:topic", "research:trends", "research:competitors",
    "research:audience", "research:fact-check", "research:market",
)
REQUIRED_RESEARCH_MODULES = tuple(name for name, _dependencies in DEFAULT_RESEARCH_PIPELINE)
_SOURCE_CONTAINER_KEYS = {
    "citations", "evidence", "references", "source_evidence",
    "source_refs", "source_urls", "sources",
}
_SOURCE_URL_KEYS = {"canonical_url", "citation_url", "source_url", "source_uri"}
_URL_CONTEXT_KEYS = {"url", "uri"}


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _extract_source_urls(value: Any) -> tuple[str, ...]:
    """Extract explicit HTTP(S) references only from source/evidence-shaped fields."""
    found: set[str] = set()

    def visit(item: Any, *, source_context: bool = False, depth: int = 0) -> None:
        if depth > 20:
            return
        if isinstance(item, Mapping):
            for key, child in item.items():
                normalized_key = str(key).casefold()
                if normalized_key in _SOURCE_URL_KEYS:
                    if _is_http_url(child):
                        found.add(child.strip())
                    continue
                if normalized_key in _SOURCE_CONTAINER_KEYS:
                    visit(child, source_context=True, depth=depth + 1)
                    continue
                if source_context and normalized_key in _URL_CONTEXT_KEYS:
                    if _is_http_url(child):
                        found.add(child.strip())
                    continue
                if isinstance(child, (Mapping, list, tuple)):
                    visit(child, source_context=source_context, depth=depth + 1)
                elif source_context and isinstance(child, str) and _is_http_url(child):
                    found.add(child.strip())
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child, source_context=source_context, depth=depth + 1)
        elif source_context and isinstance(item, str) and _is_http_url(item):
            found.add(item.strip())

    visit(value)
    return tuple(sorted(found))


class ResearchAgent:
    """Single CEO-facing entry point for the existing Layer 02 research workflow.

    module_functions must contain concrete callables for each step in
    DEFAULT_RESEARCH_PIPELINE. Each receives the task's scoped context as keyword
    arguments. A run is certified complete only when all workflow steps succeed
    and outputs include real HTTP(S) source references.
    """

    def __init__(
        self,
        module_functions: Mapping[str, Callable[..., Any]],
        *,
        planner_factory: Callable[[], PlannerManager] = PlannerManager,
        orchestrator_factory: Callable[[], OrchestratorManager] = OrchestratorManager,
    ) -> None:
        supplied = dict(module_functions)
        required = set(REQUIRED_RESEARCH_MODULES)
        missing = sorted(required - set(supplied))
        unexpected = sorted(set(supplied) - required)
        details = []
        if missing:
            details.append("missing Layer 02 modules: " + ", ".join(missing))
        if unexpected:
            details.append("unused module bindings: " + ", ".join(unexpected))
        if details:
            raise ValueError("; ".join(details))
        non_callables = sorted(name for name, func in supplied.items() if not callable(func))
        if non_callables:
            raise TypeError("Layer 02 module bindings must be callable: " + ", ".join(non_callables))
        self._module_functions = supplied
        self._planner_factory = planner_factory
        self._orchestrator_factory = orchestrator_factory

    def manifest(self) -> AgentManifest:
        """Return the canonical registered role for this implementation."""
        return AgentManifest(
            role=AgentRole.RESEARCH,
            capabilities=RESEARCH_CAPABILITIES,
            version=RESEARCH_AGENT_VERSION,
            required_tools=("layer02.research_pipeline",),
        )

    def execute(self, agent: AgentManifest, task: AgentTask) -> AgentResult:
        """Plan, run, validate and report one bounded research task."""
        if agent.role != AgentRole.RESEARCH:
            return self._blocked(task, "ResearchAgent received a non-research manifest.")
        if not agent.enabled:
            return self._blocked(task, "Research Agent is disabled.")
        if task.capability not in agent.capabilities:
            return self._blocked(task, "Task capability is not declared by the Research Agent.")

        raw_topic = task.input_data.get("topic", task.instruction)
        topic = raw_topic.strip() if isinstance(raw_topic, str) else ""
        raw_niche = task.input_data.get("niche", "general")
        niche = raw_niche.strip() if isinstance(raw_niche, str) else ""
        if not topic:
            return self._blocked(task, "Research task requires a non-empty topic.")
        if not niche:
            return self._blocked(task, "Research task requires a non-empty niche.")

        try:
            target_confidence = float(task.input_data.get("target_confidence", 0.8))
        except (TypeError, ValueError):
            return self._blocked(task, "target_confidence must be a number between 0 and 1.")
        if not 0.0 <= target_confidence <= 1.0:
            return self._blocked(task, "target_confidence must be between 0 and 1.")

        # Caller-supplied IDs cannot override CEO-authorized scope.
        context = dict(task.input_data)
        context.update({
            "topic": topic,
            "niche": niche,
            "goal_id": task.goal_id,
            "task_id": task.task_id,
            "tenant_id": task.scope.tenant_id,
            "workspace_id": task.scope.workspace_id,
            "brand_id": task.scope.brand_id,
            "acceptance_criteria": list(task.acceptance_criteria),
        })

        try:
            planner = self._planner_factory()
            plan = planner.create_plan(
                topic=topic,
                goal_title=task.instruction,
                niche=niche,
                target_confidence=target_confidence,
            )
            orchestrator = self._orchestrator_factory()
            execution = orchestrator.create_execution(
                topic=topic, workflow_name="default_research", niche=niche,
            )
            pipeline_result = orchestrator.execute(
                execution,
                module_funcs=self._module_functions,
                custom_context=context,
            )
            module_results = pipeline_result.module_results
            source_urls = _extract_source_urls(module_results)
            confidence = float(pipeline_result.overall_confidence)
            confidence = max(0.0, min(1.0, confidence))
            trace = AgentEvidence(
                kind="layer02_execution_trace",
                reference=f"layer02://research/{pipeline_result.execution_id}",
                description="Layer 02 research workflow execution record.",
                confidence=confidence,
            )
            evidence = tuple(
                AgentEvidence(
                    kind="source_url",
                    reference=url,
                    description="Source URL returned by a Layer 02 research module.",
                )
                for url in source_urls
            ) + (trace,)

            output = {
                "topic": topic,
                "niche": niche,
                "research_plan": plan.to_dict(),
                "pipeline": pipeline_result.to_dict(),
                "module_results": module_results,
                "source_urls": list(source_urls),
                "completed_modules": list(pipeline_result.completed_modules),
                "failed_modules": list(pipeline_result.failed_modules),
                "duration_seconds": pipeline_result.total_duration_sec,
            }
            errors = list(pipeline_result.error_summary)
            if pipeline_result.status == "failed" or not pipeline_result.completed_modules:
                status = AgentRunStatus.FAILED
                if not errors:
                    errors.append("Layer 02 research pipeline did not complete any module.")
            elif pipeline_result.status != "completed":
                status = AgentRunStatus.PARTIAL
            elif not source_urls:
                status = AgentRunStatus.PARTIAL
                errors.append(
                    "Research modules returned no well-formed HTTP(S) source URLs; "
                    "the run cannot be certified as completed."
                )
            else:
                status = AgentRunStatus.COMPLETED

            if status == AgentRunStatus.COMPLETED:
                summary = (
                    f"Research completed for '{topic}' using "
                    f"{len(pipeline_result.completed_modules)} Layer 02 modules and "
                    f"{len(source_urls)} distinct source URLs."
                )
            elif status == AgentRunStatus.FAILED:
                summary = f"Research failed for '{topic}'; inspect module errors and execution trace."
            else:
                summary = (
                    f"Research for '{topic}' is partial; "
                    f"{len(source_urls)} verifiable source URLs were collected."
                )

            return AgentResult(
                task_id=task.task_id,
                agent_role=AgentRole.RESEARCH,
                status=status,
                summary=summary,
                output=output,
                evidence=evidence,
                confidence=confidence,
                errors=tuple(errors),
                artifacts=(trace.reference,),
            )
        except Exception as exc:
            return AgentResult(
                task_id=task.task_id,
                agent_role=AgentRole.RESEARCH,
                status=AgentRunStatus.FAILED,
                summary="Research agent execution failed before evidence-backed completion.",
                errors=(f"{type(exc).__name__}: {str(exc)[:300]}",),
            )

    @staticmethod
    def _blocked(task: AgentTask, reason: str) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_role=AgentRole.RESEARCH,
            status=AgentRunStatus.BLOCKED,
            summary="Research task was blocked by agent contract validation.",
            errors=(reason,),
        )
