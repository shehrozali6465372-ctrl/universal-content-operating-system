"""Tests for Research Planner exceptions."""

from layers.layer02_research.modules.research_planner.exceptions import (
    ResearchPlannerError,
    GoalCreationError,
    PlanOptimizationError,
    DependencyError,
    TaskDecompositionError,
    ResourceEstimationError,
    InvalidPlanError,
)


class TestExceptions:
    def test_base_exception(self):
        try:
            raise ResearchPlannerError("test error")
        except ResearchPlannerError as e:
            assert str(e) == "test error"

    def test_goal_creation_error(self):
        try:
            raise GoalCreationError("failed")
        except ResearchPlannerError:
            pass  # inherits from base

    def test_plan_optimization_error(self):
        try:
            raise PlanOptimizationError("bad plan")
        except ResearchPlannerError:
            pass

    def test_dependency_error(self):
        try:
            raise DependencyError("cycle detected")
        except ResearchPlannerError:
            pass

    def test_task_decomposition_error(self):
        try:
            raise TaskDecompositionError("decomp failed")
        except ResearchPlannerError:
            pass

    def test_resource_estimation_error(self):
        try:
            raise ResourceEstimationError("est failed")
        except ResearchPlannerError:
            pass

    def test_invalid_plan_error(self):
        try:
            raise InvalidPlanError("invalid")
        except ResearchPlannerError:
            pass
