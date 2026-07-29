"""PromptOptimizer — Optimize AI prompts based on performance feedback."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import PromptTemplate


class PromptOptimizer:
    """Manage and optimize prompt templates."""

    def __init__(self) -> None:
        self._prompts: Dict[str, PromptTemplate] = {}
        self._lock = threading.RLock()

    def register_prompt(self, name: str, category: str,
                        template: str) -> PromptTemplate:
        prompt = PromptTemplate(name, category, template)
        with self._lock:
            self._prompts[prompt.prompt_id] = prompt
        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
        return self._prompts.get(prompt_id)

    def get_prompts_by_category(self, category: str) -> List[PromptTemplate]:
        return [p for p in self._prompts.values() if p.category == category]

    def get_all_prompts(self) -> List[PromptTemplate]:
        return list(self._prompts.values())

    def record_use(self, prompt_id: str, score: float = 0.0) -> bool:
        with self._lock:
            prompt = self._prompts.get(prompt_id)
            if not prompt:
                return False
            prompt.use_count += 1
            prompt.performance_score = (
                (prompt.performance_score * (prompt.use_count - 1) + score) /
                prompt.use_count
            )
        return True

    def optimize(self, prompt_id: str, new_template: str) -> bool:
        with self._lock:
            prompt = self._prompts.get(prompt_id)
            if not prompt:
                return False
            old_version = prompt.version
            major, minor = old_version.split(".")
            prompt.version = f"{major}.{int(minor) + 1}"
            prompt.template = new_template
        return True

    def get_best_prompts(self, category: str, top_k: int = 3) -> List[PromptTemplate]:
        prompts = self.get_prompts_by_category(category)
        prompts.sort(key=lambda p: p.performance_score, reverse=True)
        return prompts[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_prompts": len(self._prompts),
                "categories": len(set(p.category for p in self._prompts.values())),
                "total_uses": sum(p.use_count for p in self._prompts.values()),
            }
