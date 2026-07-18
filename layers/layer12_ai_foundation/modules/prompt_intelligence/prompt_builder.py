"""PromptBuilder — construct prompts from components programmatically."""
from __future__ import annotations

from typing import Any, Dict, List


class PromptBuilder:
    """Build prompts programmatically from components."""

    def __init__(self) -> None:
        self._components: List[str] = []
        self._variables: Dict[str, str] = {}
        self._system: str = ""

    def set_system(self, system_prompt: str) -> "PromptBuilder":
        self._system = system_prompt
        return self

    def add_instruction(self, instruction: str) -> "PromptBuilder":
        self._components.append(f"Instruction: {instruction}")
        return self

    def add_context(self, context: str) -> "PromptBuilder":
        self._components.append(f"Context: {context}")
        return self

    def add_constraint(self, constraint: str) -> "PromptBuilder":
        self._components.append(f"Constraint: {constraint}")
        return self

    def add_example(self, example: str) -> "PromptBuilder":
        self._components.append(f"Example: {example}")
        return self

    def add_input(self, input_text: str) -> "PromptBuilder":
        self._components.append(f"Input: {input_text}")
        return self

    def set_variable(self, key: str, value: str) -> "PromptBuilder":
        self._variables[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        prompt_text = "\n".join(self._components)
        for key, value in self._variables.items():
            prompt_text = prompt_text.replace(f"{{{key}}}", value)
        return {"system": self._system, "prompt": prompt_text,
                "components": len(self._components)}

    def reset(self) -> None:
        self._components.clear()
        self._variables.clear()
        self._system = ""
