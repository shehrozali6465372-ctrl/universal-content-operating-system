"""Custom exceptions for Learning Connector."""


class LearningError(Exception):
    """Base learning error."""


class KnowledgeError(LearningError):
    """Knowledge base error."""


class PatternRecognitionError(LearningError):
    """Pattern recognition error."""


class MemoryError(LearningError):
    """Memory connector error."""


class VersionError(LearningError):
    """Version management error."""


class RecommendationError(LearningError):
    """Recommendation engine error."""


class ImprovementError(LearningError):
    """Self-improvement error."""


class CollectionError(LearningError):
    """Data collection error."""


class AnalysisError(LearningError):
    """Performance analysis error."""


class DecisionError(LearningError):
    """Decision engine error."""


class StrategyError(LearningError):
    """Strategy learning error."""
