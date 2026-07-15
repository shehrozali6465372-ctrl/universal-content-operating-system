"""Content Planner — Custom Exceptions."""


class ContentPlannerError(Exception):
    """Base exception for Content Planner."""


class InvalidPlanError(ContentPlannerError):
    """Raised when a plan fails validation."""


class GoalConflictError(ContentPlannerError):
    """Raised when goals are contradictory."""


class PlatformConstraintError(ContentPlannerError):
    """Raised when platform constraints cannot be satisfied."""


class AudienceMismatchError(ContentPlannerError):
    """Raised when audience data is inconsistent with content goals."""
