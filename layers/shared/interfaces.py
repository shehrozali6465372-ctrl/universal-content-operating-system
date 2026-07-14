"""
Layer Contracts — Frozen Interfaces

Every layer must implement these base interfaces.
This enables easy provider swapping and testing.

Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IResearchModule(ABC):
    """Interface for all research modules."""

    @abstractmethod
    def get_module_name(self) -> str: ...

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def get_confidence(self) -> float: ...

    @abstractmethod
    def get_evidence(self) -> List[str]: ...


class IWritingModule(ABC):
    """Interface for content generation modules."""

    @abstractmethod
    def generate(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def get_module_name(self) -> str: ...

    @abstractmethod
    def get_supported_styles(self) -> List[str]: ...


class IPublisher(ABC):
    """Interface for platform publishers."""

    @abstractmethod
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def get_platform(self) -> str: ...

    @abstractmethod
    def is_healthy(self) -> bool: ...


class IAnalyticsProvider(ABC):
    """Interface for analytics collection."""

    @abstractmethod
    def collect(self, post_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    def get_metrics(self, post_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...


class ILearningModule(ABC):
    """Interface for self-learning modules."""

    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def get_recommendations(self) -> List[Dict]: ...

    @abstractmethod
    def update_strategy(self, feedback: Dict[str, Any]) -> bool: ...
