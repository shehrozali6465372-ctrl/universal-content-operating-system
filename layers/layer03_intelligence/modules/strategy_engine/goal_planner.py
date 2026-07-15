"""Goal Planner — Multi-goal planning with priorities and dependencies."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional


class Goal:
    """A single goal with priority and dependencies."""
    __slots__ = ("goal_id", "name", "description", "priority", "status",
                 "dependencies", "deadline", "weight", "progress", "metadata")

    def __init__(self, name: str = "", priority: str = "medium") -> None:
        self.goal_id = f"goal_{next(_GOAL_COUNTER)}"
        self.name = name
        self.description = ""
        self.priority = priority
        self.status = "pending"
        self.dependencies: List[str] = []
        self.deadline: Optional[float] = None
        self.weight = 1.0
        self.progress = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id, "name": self.name, "priority": self.priority,
            "status": self.status, "dependencies": self.dependencies,
            "progress": round(self.progress, 3), "weight": self.weight,
        }


class GoalPlan:
    """A plan containing ordered goals."""
    __slots__ = ("plan_id", "goals", "execution_order", "critical_path",
                 "total_weight", "estimated_time", "goal_count")

    def __init__(self, plan_id: str = "") -> None:
        self.plan_id = plan_id or f"gplan_{int(time.time()*1000) % 10000000}"
        self.goals: List[Goal] = []
        self.execution_order: List[str] = []
        self.critical_path: List[str] = []
        self.total_weight = 0.0
        self.estimated_time = 0.0
        self.goal_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_count": self.goal_count,
            "execution_order": self.execution_order,
            "critical_path": self.critical_path,
            "total_weight": round(self.total_weight, 3),
            "estimated_time": round(self.estimated_time, 2),
        }


_GOAL_COUNTER = itertools.count(1)


class GoalPlanner:
    """Plans and orders goals with dependency resolution."""

    PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "background": 4}

    def __init__(self) -> None:
        self._plans: Dict[str, GoalPlan] = {}

    def create_goals(self, goal_configs: List[Dict[str, Any]]) -> List[Goal]:
        """Create goals from configuration dicts."""
        goals: List[Goal] = []
        for cfg in goal_configs:
            g = Goal(name=cfg.get("name", ""), priority=cfg.get("priority", "medium"))
            g.description = cfg.get("description", "")
            g.dependencies = cfg.get("dependencies", [])
            g.weight = cfg.get("weight", 1.0)
            g.metadata = cfg.get("metadata", {})
            goals.append(g)
        return goals

    def plan(self, goals: List[Goal]) -> GoalPlan:
        """Resolve dependencies and create execution plan."""
        plan = GoalPlan()
        plan.goals = goals
        plan.goal_count = len(goals)
        plan.total_weight = sum(g.weight for g in goals)

        id_map = {g.goal_id: g for g in goals}

        # Topological sort (Kahn's algorithm)
        in_degree: Dict[str, int] = {g.goal_id: 0 for g in goals}
        dependents: Dict[str, List[str]] = {g.goal_id: [] for g in goals}
        for g in goals:
            for dep_id in g.dependencies:
                if dep_id in id_map:
                    in_degree[g.goal_id] += 1
                    dependents[dep_id].append(g.goal_id)

        queue = [gid for gid, deg in in_degree.items() if deg == 0]
        resolved: List[str] = []
        while queue:
            gid = queue.pop(0)
            resolved.append(gid)
            for dependent in dependents[gid]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        plan.execution_order = resolved

        # Critical path
        plan.critical_path = self._find_critical_path(goals, id_map)

        # Estimate time (2 min per goal, +0.5 per dependency)
        plan.estimated_time = sum(2 + len(g.dependencies) * 0.5 for g in goals)

        self._plans[plan.plan_id] = plan
        return plan

    def reprioritize(self, plan: GoalPlan, new_priorities: Dict[str, str]) -> GoalPlan:
        """Update goal priorities and re-sort execution order."""
        for g in plan.goals:
            if g.goal_id in new_priorities:
                g.priority = new_priorities[g.goal_id]
        return plan

    def update_progress(self, plan: GoalPlan, goal_id: str, progress: float) -> Optional[Goal]:
        """Update progress for a specific goal."""
        for g in plan.goals:
            if g.goal_id == goal_id:
                g.progress = min(1.0, max(0.0, progress))
                if g.progress >= 1.0:
                    g.status = "completed"
                elif g.progress > 0:
                    g.status = "in_progress"
                return g
        return None

    def get_blocked_goals(self, plan: GoalPlan) -> List[Goal]:
        """Return goals that cannot start due to unmet dependencies."""
        completed = {g.goal_id for g in plan.goals if g.status == "completed"}
        blocked: List[Goal] = []
        for g in plan.goals:
            if g.status != "pending":
                continue
            for dep in g.dependencies:
                if dep not in completed:
                    blocked.append(g)
                    break
        return blocked

    def get_plan(self, plan_id: str) -> Optional[GoalPlan]:
        return self._plans.get(plan_id)

    def _find_critical_path(self, goals: List[Goal], id_map: Dict[str, Any]) -> List[str]:
        """Find the critical path using DFS with cycle detection."""
        visited: set = set()
        in_stack: set = set()
        memo: Dict[str, int] = {}
        path_memo: Dict[str, List[str]] = {}

        def _dfs(gid: str) -> int:
            if gid in memo:
                return memo[gid]
            if gid in in_stack:
                return 0  # cycle protection
            g = id_map.get(gid)
            if g is None or not g.dependencies:
                memo[gid] = 0
                path_memo[gid] = [gid]
                return 0
            in_stack.add(gid)
            best_depth = 0
            best_path: List[str] = []
            for dep in g.dependencies:
                if dep in id_map:
                    d = _dfs(dep)
                    p = path_memo.get(dep, [])
                    if d > best_depth or (d == best_depth and len(p) > len(best_path)):
                        best_depth = d
                        best_path = p
            in_stack.remove(gid)
            memo[gid] = best_depth + 1
            path_memo[gid] = best_path + [gid]
            visited.add(gid)
            return memo[gid]

        for g in goals:
            _dfs(g.goal_id)

        if not path_memo:
            return []
        best_goal = max(path_memo, key=lambda k: memo.get(k, 0))
        return path_memo.get(best_goal, [best_goal])
