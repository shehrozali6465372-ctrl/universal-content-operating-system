"""SystemPromptManager — manage system prompts for different roles and contexts."""
from __future__ import annotations

from typing import Dict, List


class SystemPromptManager:
    """Manage system prompts for different AI roles and contexts."""

    DEFAULT_ROLES: Dict[str, str] = {
        "assistant": "You are a helpful, harmless, and honest AI assistant.",
        "writer": "You are a skilled professional writer. Write engaging, high-quality content.",
        "coder": "You are an expert programmer. Write clean, efficient, well-documented code.",
        "analyst": "You are a data analyst. Provide clear, data-driven insights.",
        "critic": "You are a quality critic. Review content and provide constructive feedback.",
        "strategist": "You are a strategic planner. Develop actionable plans with clear steps.",
        "researcher": "You are a thorough researcher. Provide accurate, well-sourced information.",
        "creative": "You are a creative director. Generate innovative, original ideas.",
    }

    def __init__(self) -> None:
        self._roles: Dict[str, str] = dict(self.DEFAULT_ROLES)
        self._custom: Dict[str, str] = {}

    def get_prompt(self, role: str, extra: str = "") -> str:
        prompt = self._custom.get(role, self._roles.get(role, f"You are a helpful {role}."))
        if extra:
            prompt += f" {extra}"
        return prompt

    def register_role(self, role: str, prompt: str) -> None:
        self._custom[role] = prompt

    def remove_role(self, role: str) -> bool:
        if role in self._custom:
            del self._custom[role]
            return True
        return False

    def list_roles(self) -> List[str]:
        return list(set(list(self._roles.keys()) + list(self._custom.keys())))

    def to_dict(self) -> Dict[str, str]:
        all_roles = dict(self._roles)
        all_roles.update(self._custom)
        return all_roles
