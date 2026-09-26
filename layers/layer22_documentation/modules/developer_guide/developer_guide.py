"""Production-safe developer guide generation."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any, Dict, List


class DeveloperGuide:
    """Build deterministic developer onboarding documentation."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sections: List[Dict[str, Any]] = []
        self._prerequisites: List[str] = []
        self._conventions: List[str] = []

    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-blank string")
        return value.strip()

    @staticmethod
    def _require_order(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("order must be an integer")
        return value

    def add_section(self, title: str, content: str, order: int = 0) -> None:
        section = {
            "title": self._require_text(title, "title"),
            "content": self._require_text(content, "content"),
            "order": self._require_order(order),
        }
        with self._lock:
            if any(item["title"] == section["title"] for item in self._sections):
                raise ValueError(f"duplicate section: {section['title']}")
            self._sections.append(section)

    def add_prerequisite(self, prereq: str) -> None:
        value = self._require_text(prereq, "prereq")
        with self._lock:
            if value not in self._prerequisites:
                self._prerequisites.append(value)

    def add_convention(self, convention: str) -> None:
        value = self._require_text(convention, "convention")
        with self._lock:
            if value not in self._conventions:
                self._conventions.append(value)

    def _sorted_sections(self) -> List[Dict[str, Any]]:
        return sorted(self._sections, key=lambda item: (item["order"], item["title"]))

    def generate(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "sections": deepcopy(self._sorted_sections()),
                "prerequisites": deepcopy(self._prerequisites),
                "conventions": deepcopy(self._conventions),
            }

    def generate_markdown(self) -> str:
        with self._lock:
            sections = deepcopy(self._sorted_sections())
            prerequisites = deepcopy(self._prerequisites)
        lines = ["# Developer Guide", ""]
        if prerequisites:
            lines.append("## Prerequisites")
            lines.extend(f"- {item}" for item in prerequisites)
            lines.append("")
        for section in sections:
            lines.extend([f"## {section['title']}", section["content"], ""])
        return "\n".join(lines)
