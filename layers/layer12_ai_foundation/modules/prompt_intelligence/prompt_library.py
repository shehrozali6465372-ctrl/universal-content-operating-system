"""PromptLibrary — collection of reusable prompt templates."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import PromptTemplate


class PromptLibrary:
    """Library of reusable prompt templates organized by category."""

    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        defaults = [
            PromptTemplate(name="blog_writer", template="Write a {length} blog post about {topic}. Target audience: {audience}.",
                           variables=["length", "topic", "audience"], category="writing", tags=["blog", "content"]),
            PromptTemplate(name="social_post", template="Create a {platform} post about {topic}. Tone: {tone}.",
                           variables=["platform", "topic", "tone"], category="social", tags=["social", "post"]),
            PromptTemplate(name="code_review", template="Review this code for issues:\n{code}\nLanguage: {language}",
                           variables=["code", "language"], category="coding", tags=["code", "review"]),
            PromptTemplate(name="email_writer", template="Write a {email_type} email to {recipient} about {topic}.",
                           variables=["email_type", "recipient", "topic"], category="writing", tags=["email"]),
            PromptTemplate(name="summarizer", template="Summarize the following text in {length} words:\n{text}",
                           variables=["length", "text"], category="analysis", tags=["summary"]),
        ]
        for t in defaults:
            self._templates[t.name] = t

    def add(self, template: PromptTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[PromptTemplate]:
        return self._templates.get(name)

    def remove(self, name: str) -> bool:
        return self._templates.pop(name, None) is not None

    def list_templates(self) -> List[str]:
        return list(self._templates.keys())

    def search(self, category: str = "", tags: Optional[List[str]] = None) -> List[PromptTemplate]:
        results = list(self._templates.values())
        if category:
            results = [t for t in results if t.category == category]
        if tags:
            results = [t for t in results if any(tag in t.tags for tag in tags)]
        return results

    def count(self) -> int:
        return len(self._templates)

    def to_dict(self) -> Dict[str, Any]:
        return {name: t.to_dict() for name, t in self._templates.items()}
