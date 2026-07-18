"""Data models for Prompt Intelligence."""
from __future__ import annotations

import uuid
import time
from typing import Any, Dict, List
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """A reusable prompt template."""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    template: str = ""
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    score: float = 0.0
    usage_count: int = 0
    created_at: float = field(default_factory=time.time)

    def render(self, **kwargs: Any) -> str:
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id, "name": self.name,
            "template": self.template, "variables": self.variables,
            "category": self.category, "tags": self.tags,
            "score": self.score, "usage_count": self.usage_count,
        }


@dataclass
class FewShotExample:
    """A few-shot example for in-context learning."""
    example_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    input_text: str = ""
    output_text: str = ""
    category: str = ""
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "example_id": self.example_id, "input_text": self.input_text[:100],
            "output_text": self.output_text[:100], "category": self.category,
            "relevance_score": self.relevance_score,
        }


@dataclass
class OptimizedPrompt:
    """Result of prompt optimization."""
    original: str = ""
    optimized: str = ""
    improvement_score: float = 0.0
    optimizations_applied: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original": self.original[:200], "optimized": self.optimized[:200],
            "improvement_score": self.improvement_score,
            "optimizations": self.optimizations_applied,
        }
