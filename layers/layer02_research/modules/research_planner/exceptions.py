"""
Research Planner Exceptions
Layer 2: Research Engine — Module 9
"""


class ResearchPlannerError(Exception):
    """Base exception for Research Planner module."""


class GoalCreationError(ResearchPlannerError):
    """Raised when goal creation fails."""


class PlanOptimizationError(ResearchPlannerError):
    """Raised when plan optimization fails."""


class DependencyError(ResearchPlannerError):
    """Raised when dependency resolution fails."""


class TaskDecompositionError(ResearchPlannerError):
    """Raised when task decomposition fails."""


class ResourceEstimationError(ResearchPlannerError):
    """Raised when resource estimation fails."""


class InvalidPlanError(ResearchPlannerError):
    """Raised when a plan is invalid or malformed."""
