"""
Shared Data Models

Frozen interfaces used across all layers.
These models should NOT be modified without versioning.

Version: 1.0.0
"""

from layers.shared.models.topic import Topic, TopicScore
from layers.shared.models.confidence import ConfidenceResult
from layers.shared.models.evidence import Evidence, EvidenceBundle
from layers.shared.models.decision import DecisionTrace, DecisionRecord
from layers.shared.models.content import ContentPost, ContentVariant
from layers.shared.models.analytics import AnalyticsSnapshot, EngagementMetrics
from layers.shared.models.event import Event, EventType
from layers.shared.llm_provider import BaseLLMProvider, LLMResponse, LLMFactory

__all__ = [
    "Topic", "TopicScore",
    "ConfidenceResult",
    "Evidence", "EvidenceBundle",
    "DecisionTrace", "DecisionRecord",
    "ContentPost", "ContentVariant",
    "AnalyticsSnapshot", "EngagementMetrics",
    "Event", "EventType",
    "BaseLLMProvider", "LLMResponse", "LLMFactory",
]
