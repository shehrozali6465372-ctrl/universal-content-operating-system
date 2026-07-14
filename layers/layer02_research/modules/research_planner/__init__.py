"""
Research Planner Module
Layer 2: Research Engine — Module 9

Planning brain for research operations:
- Goal management
- Research plan creation
- Task decomposition
- Dependency analysis
- Priority assignment
- Resource estimation
- Plan optimization
"""

from layers.layer02_research.modules.research_planner.planner_manager import PlannerManager
from layers.layer02_research.modules.research_planner.goal_manager import GoalManager, ResearchGoal
from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan
from layers.layer02_research.modules.research_planner.task_decomposer import TaskDecomposer
from layers.layer02_research.modules.research_planner.dependency_graph import DependencyGraph
from layers.layer02_research.modules.research_planner.priority_engine import PriorityEngine
from layers.layer02_research.modules.research_planner.resource_estimator import ResourceEstimator, ResourceEstimate
from layers.layer02_research.modules.research_planner.plan_optimizer import PlanOptimizer, OptimizedPlan, ExecutionWave
from layers.layer02_research.modules.research_planner.exceptions import (
    ResearchPlannerError, GoalCreationError, PlanOptimizationError,
    DependencyError, TaskDecompositionError, ResourceEstimationError,
    InvalidPlanError,
)

__all__ = [
    "PlannerManager",
    "GoalManager",
    "ResearchGoal",
    "PlanTask",
    "ResearchPlan",
    "TaskDecomposer",
    "DependencyGraph",
    "PriorityEngine",
    "ResourceEstimator",
    "ResourceEstimate",
    "PlanOptimizer",
    "OptimizedPlan",
    "ExecutionWave",
    "ResearchPlannerError",
    "GoalCreationError",
    "PlanOptimizationError",
    "DependencyError",
    "TaskDecompositionError",
    "ResourceEstimationError",
    "InvalidPlanError",
]
