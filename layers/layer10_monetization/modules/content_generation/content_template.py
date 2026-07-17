"""ContentTemplate — Reusable content templates."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List, Optional

_CT_COUNTER = itertools.count(1)


class ContentTemplate:
    """A reusable content template."""

    __slots__ = ("template_id", "name", "platform", "content_type",
                 "structure", "variables", "metadata")

    def __init__(self, name: str = "", platform: str = "") -> None:
        self.template_id: str = f"tpl_{next(_CT_COUNTER)}"
        self.name = name
        self.platform = platform
        self.content_type: str = "social_post"
        self.structure: List[Dict[str, str]] = []
        self.variables: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}

    def add_section(self, section_type: str, content: str) -> None:
        self.structure.append({"type": section_type, "content": content})

    def render(self, variables: Optional[Dict[str, str]] = None) -> str:
        vars_ = {**self.variables, **(variables or {})}
        parts = []
        for section in self.structure:
            text = section["content"]
            for k, v in vars_.items():
                text = text.replace(f"{{{{{k}}}}}", v)
            parts.append(text)
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id, "name": self.name,
            "platform": self.platform, "sections": len(self.structure),
        }


class TemplateLibrary:
    """Library of content templates."""

    def __init__(self) -> None:
        self._templates: List[ContentTemplate] = []

    def add(self, template: ContentTemplate) -> None:
        self._templates.append(template)

    def get_by_platform(self, platform: str) -> List[ContentTemplate]:
        return [t for t in self._templates if t.platform == platform]

    def get_by_type(self, content_type: str) -> List[ContentTemplate]:
        return [t for t in self._templates if t.content_type == content_type]

    def get(self, template_id: str) -> Optional[ContentTemplate]:
        for t in self._templates:
            if t.template_id == template_id:
                return t
        return None

    def get_all(self) -> List[ContentTemplate]:
        return list(self._templates)

    def get_stats(self) -> Dict[str, Any]:
        platforms = {}
        for t in self._templates:
            platforms[t.platform] = platforms.get(t.platform, 0) + 1
        return {"total": len(self._templates), "by_platform": platforms}
