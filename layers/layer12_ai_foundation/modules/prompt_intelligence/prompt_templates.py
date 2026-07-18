"""PromptTemplates — template engine for dynamic prompt generation."""
from __future__ import annotations

import re
from typing import Any, Dict, List


class PromptTemplates:
    """Template engine for dynamic prompt generation."""

    def __init__(self) -> None:
        self._templates: Dict[str, str] = {}

    def register(self, name: str, template: str) -> None:
        self._templates[name] = template

    def render(self, name: str, **kwargs: Any) -> str:
        template = self._templates.get(name, "")
        if not template:
            return ""
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        # Check for unresolved variables
        unresolved = re.findall(r"\{(\w+)\}", result)
        return result

    def list_variables(self, name: str) -> List[str]:
        template = self._templates.get(name, "")
        return re.findall(r"\{(\w+)\}", template)

    def validate(self, name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        required = self.list_variables(name)
        provided = set(variables.keys())
        missing = [v for v in required if v not in provided]
        return {"valid": len(missing) == 0, "missing": missing, "required": required}

    def get(self, name: str) -> str:
        return self._templates.get(name, "")

    def remove(self, name: str) -> bool:
        return self._templates.pop(name, None) is not None

    def count(self) -> int:
        return len(self._templates)

    def to_dict(self) -> Dict[str, str]:
        return dict(self._templates)
