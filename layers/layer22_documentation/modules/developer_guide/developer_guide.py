"""DeveloperGuide — developer onboarding and contribution guide."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class DeveloperGuide:
    def __init__(self) -> None:
        self._sections: List[Dict[str, Any]] = []
        self._prerequisites: List[str] = []
        self._conventions: List[str] = []

    def add_section(self, title: str, content: str, order: int = 0) -> None:
        self._sections.append({"title": title, "content": content, "order": order})

    def add_prerequisite(self, prereq: str) -> None:
        self._prerequisites.append(prereq)

    def add_convention(self, convention: str) -> None:
        self._conventions.append(convention)

    def generate(self) -> Dict[str, Any]:
        sorted_sections = sorted(self._sections, key=lambda s: s["order"])
        return {"sections": sorted_sections, "prerequisites": self._prerequisites,
                "conventions": self._conventions}

    def generate_markdown(self) -> str:
        lines = ["# Developer Guide", ""]
        if self._prerequisites:
            lines.append("## Prerequisites")
            for p in self._prerequisites:
                lines.append(f"- {p}")
            lines.append("")
        for section in sorted(self._sections, key=lambda s: s["order"]):
            lines.append(f"## {section['title']}")
            lines.append(section["content"])
            lines.append("")
        return "\n".join(lines)
