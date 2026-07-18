"""knowledge_repository.py — Knowledge repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class KnowledgeEntity(BaseEntity):
    __slots__ = ("topic", "content", "category", "confidence", "sources")

    def __init__(self, topic: str, content: str = "", category: str = "") -> None:
        super().__init__()
        self.topic = topic
        self.content = content
        self.category = category
        self.confidence: float = 0.5
        self.sources: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"topic": self.topic, "category": self.category,
                      "confidence": self.confidence})
        return base


class KnowledgeRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("knowledge")

    def find_by_category(self, category: str) -> List[KnowledgeEntity]:
        return self.find(category=category)

    def find_by_topic(self, topic: str) -> List[KnowledgeEntity]:
        return self.find(topic=topic)
