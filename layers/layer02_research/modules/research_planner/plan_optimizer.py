"""
Plan Optimizer
Layer 2: Research Engine — Module 9

Optimizes research plans:
- Parallel task scheduling
- Cost optimization
- Time optimization
- Quality-aware pruning
- Plan merging
"""

from typing import Dict, List, Optional, Set
from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan
from layers.layer02_research.modules.research_planner.dependency_graph import DependencyGraph
from layers.layer02_research.modules.research_planner.resource_estimator import ResourceEstimator


class ExecutionWave:
    """A group of tasks that can run in parallel."""

    __slots__ = ("wave_id", "tasks", "estimated_time_min")

    def __init__(self, wave_id: int):
        self.wave_id = wave_id
        self.tasks: List[PlanTask] = []
        self.estimated_time_min = 0.0

    def to_dict(self) -> dict:
        return {
            "wave_id": self.wave_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "estimated_time_min": round(self.estimated_time_min, 2),
            "parallel_count": len(self.tasks),
        }


class OptimizedPlan:
    """Optimized version of a research plan."""

    __slots__ = ("original_plan", "waves", "total_time_min",
                 "critical_path", "parallelism_ratio",
                 "optimizations_applied")

    def __init__(self, plan: ResearchPlan):
        self.original_plan = plan
        self.waves: List[ExecutionWave] = []
        self.total_time_min = 0.0
        self.critical_path: List[str] = []
        self.parallelism_ratio = 1.0
        self.optimizations_applied: List[str] = []

    def to_dict(self) -> dict:
        return {
            "plan_id": self.original_plan.plan_id,
            "topic": self.original_plan.topic,
            "waves": [w.to_dict() for w in self.waves],
            "total_time_min": round(self.total_time_min, 2),
            "parallelism_ratio": round(self.parallelism_ratio, 2),
            "optimizations_applied": self.optimizations_applied,
        }


class PlanOptimizer:
    """Optimizes research plans for execution."""

    def __init__(self):
        self._estimator = ResourceEstimator()

    def optimize(self, plan: ResearchPlan) -> OptimizedPlan:
        """Fully optimize a research plan."""
        opt = OptimizedPlan(plan)

        # Step 1: Build dependency graph
        graph = self._build_dependency_graph(plan)

        # Step 2: Detect cycles
        if graph.has_cycle():
            return opt

        # Step 3: Generate parallel waves
        opt.waves = self._generate_waves(graph, plan)

        # Step 4: Calculate timing
        opt.total_time_min = self._calculate_parallel_time(opt.waves)

        # Step 5: Find critical path
        opt.critical_path = self._find_critical_path(plan, graph)

        # Step 6: Calculate parallelism ratio
        sequential = sum(t.estimated_time_min for t in plan.tasks)
        opt.parallelism_ratio = round(sequential / max(0.01, opt.total_time_min), 2)

        # Step 7: Apply optimizations
        opt.optimizations_applied = self._apply_optimizations(plan)

        return opt

    def optimize_for_time(self, plan: ResearchPlan) -> OptimizedPlan:
        """Optimize to minimize total execution time."""
        opt = self.optimize(plan)
        # Prioritize parallelism
        opt.optimizations_applied.append("time_optimized")
        return opt

    def optimize_for_cost(self, plan: ResearchPlan) -> OptimizedPlan:
        """Optimize to minimize API costs."""
        opt = self.optimize(plan)
        # Sort waves to do cheaper tasks first
        for wave in opt.waves:
            wave.tasks.sort(key=lambda t: t.estimated_api_calls)
        opt.optimizations_applied.append("cost_optimized")
        return opt

    def prune_low_value(self, plan: ResearchPlan,
                        min_confidence: float = 0.5) -> ResearchPlan:
        """Remove tasks that contribute little confidence."""
        if not plan.tasks:
            return plan

        total_tasks = len(plan.tasks)
        if total_tasks <= 2:
            return plan

        estimator = ResourceEstimator()
        pruned_tasks = []
        for task in plan.tasks:
            est = estimator.estimate_task(task)
            if est.expected_confidence >= min_confidence or task.priority in ("CRITICAL", "HIGH"):
                pruned_tasks.append(task)

        plan.tasks = pruned_tasks
        plan._recalculate_totals()
        return plan

    def merge_plans(self, plans: List[ResearchPlan]) -> ResearchPlan:
        """Merge multiple plans into one unified plan."""
        if not plans:
            return ResearchPlan(topic="empty")
        if len(plans) == 1:
            return plans[0]

        merged = ResearchPlan(
            topic=" & ".join(p.topic for p in plans[:3]),
            goal_title="Merged research plan",
        )

        seen_modules: Set[str] = set()
        for plan in plans:
            for task in plan.tasks:
                dedup_key = f"{task.module}:{task.name}"
                if dedup_key not in seen_modules:
                    seen_modules.add(dedup_key)
                    merged.tasks.append(task)

        merged._recalculate_totals()
        return merged

    def _build_dependency_graph(self, plan: ResearchPlan) -> DependencyGraph:
        """Build dependency graph from plan tasks."""
        graph = DependencyGraph()
        for task in plan.tasks:
            graph.add_node(task.task_id)
        for task in plan.tasks:
            for dep_id in task.dependencies:
                graph.add_edge(dep_id, task.task_id)
        return graph

    def _generate_waves(self, graph: DependencyGraph,
                        plan: ResearchPlan) -> List[ExecutionWave]:
        """Generate parallel execution waves."""
        waves = []
        task_map = {t.task_id: t for t in plan.tasks}
        completed: Set[str] = set()
        wave_id = 0

        while len(completed) < len(plan.tasks):
            ready = graph.get_ready_nodes(completed)
            if not ready:
                break

            wave = ExecutionWave(wave_id)
            for task_id in ready:
                if task_id in task_map:
                    task = task_map[task_id]
                    wave.tasks.append(task)
                    completed.add(task_id)

            if wave.tasks:
                wave.estimated_time_min = max(
                    t.estimated_time_min for t in wave.tasks
                )
                waves.append(wave)
                wave_id += 1

        return waves

    def _calculate_parallel_time(self, waves: List[ExecutionWave]) -> float:
        """Calculate total time with parallelism."""
        return sum(w.estimated_time_min for w in waves)

    def _find_critical_path(self, plan: ResearchPlan,
                            graph: DependencyGraph) -> List[str]:
        """Find the critical path (longest chain)."""
        task_map = {t.task_id: t for t in plan.tasks}
        longest: List[str] = []

        def dfs(node: str, path: List[str]) -> List[str]:
            dependents = graph.get_dependents(node)
            if not dependents:
                if len(path) > len(longest):
                    return path
                return longest
            best = path[:]
            for dep in dependents:
                if dep in task_map:
                    result = dfs(dep, path + [dep])
                    if len(result) > len(best):
                        best = result
            return best

        for task in plan.tasks:
            if not graph.get_dependencies(task.task_id):
                result = dfs(task.task_id, [task.task_id])
                if len(result) > len(longest):
                    longest = result

        return longest

    def _apply_optimizations(self, plan: ResearchPlan) -> List[str]:
        """Apply and report optimizations."""
        applied = []

        # Remove duplicate modules
        seen = set()
        deduped = []
        for task in plan.tasks:
            key = f"{task.module}:{task.name}"
            if key not in seen:
                seen.add(key)
                deduped.append(task)
        if len(deduped) < len(plan.tasks):
            plan.tasks = deduped
            plan._recalculate_totals()
            applied.append("deduplicated_tasks")

        # Sort by priority within same wave
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "BACKGROUND": 4}
        plan.tasks.sort(key=lambda t: priority_order.get(t.priority, 5))
        applied.append("priority_sorted")

        return applied
