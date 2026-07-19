"""PromptBuilder — dynamic, self-improving prompt generation.

Design Rule:
    PromptBuilder aur KeyManager kabhi mix nahi honge.
    PromptBuilder → sirf prompt banaye
    KeyManager → sirf authentication + health + rate limits
"""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class PromptStyle(str, Enum):
    DIRECT = "direct"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    ZERO_SHOT = "zero_shot"
    REFLECTION = "reflection"
    PERSONA = "persona"


class PromptTemplate:
    __slots__ = ("template_id", "name", "template", "style",
                 "variables", "examples", "metadata")

    def __init__(self, name: str, template: str,
                 style: PromptStyle = PromptStyle.DIRECT) -> None:
        self.template_id = f"tmpl_{name}"
        self.name = name
        self.template = template
        self.style = style
        self.variables: List[str] = []
        self.examples: List[Dict[str, str]] = []
        self.metadata: Dict[str, Any] = {}

    def render(self, **kwargs: Any) -> str:
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id, "name": self.name,
            "style": self.style.value, "variables": self.variables,
        }


class PromptBuilder:
    """Dynamic, self-improving prompt generation.

    Har request ke liye naya, context-aware prompt banaye.
    Keys se bilkul alag — ye sirf prompt quality ke liye hai.
    """

    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}
        self._memory: List[Dict[str, Any]] = []
        self._performance: Dict[str, Dict[str, float]] = {}

    def add_template(self, template: PromptTemplate) -> None:
        self._templates[template.template_id] = template

    def build(self, task: str, style: PromptStyle = PromptStyle.DIRECT,
              context: Optional[Dict[str, Any]] = None,
              system_prompt: str = "",
              examples: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Naya prompt build karo."""
        prompt_id = str(uuid.uuid4())[:12]
        parts = []

        if system_prompt:
            parts.append({"role": "system", "content": system_prompt})

        # Chain of Thought style
        if style == PromptStyle.CHAIN_OF_THOUGHT:
            parts.append({"role": "user", "content":
                f"Think step by step.\n\n{task}"})

        # Few-shot style
        elif style == PromptStyle.FEW_SHOT:
            if examples:
                for ex in examples:
                    parts.append({"role": "user", "content": ex.get("input", "")})
                    parts.append({"role": "assistant", "content": ex.get("output", "")})
            parts.append({"role": "user", "content": task})

        # Reflection style
        elif style == PromptStyle.REFLECTION:
            parts.append({"role": "user", "content":
                f"Review and improve this:\n\n{task}\n\n"
                f"Think about what could be better before responding."})

        # Default: direct
        else:
            parts.append({"role": "user", "content": task})

        # Context inject karo
        if context:
            ctx_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
            parts.append({"role": "user", "content": f"Context:\n{ctx_str}"})

        result = {
            "prompt_id": prompt_id,
            "messages": parts,
            "style": style.value,
            "task": task[:200],
        }

        self._memory.append({"prompt_id": prompt_id, "style": style.value,
                            "task": task[:100], "time": time.time()})
        return result

    def build_text(self, task: str, style: PromptStyle = PromptStyle.DIRECT,
                   **kwargs: Any) -> str:
        """Simple text prompt return karo."""
        result = self.build(task, style, **kwargs)
        messages = result["messages"]
        return "\n".join(m.get("content", "") for m in messages)

    def record_outcome(self, prompt_id: str, success: bool,
                       quality_score: float = 0.0) -> None:
        """Prompt performance track karo for self-improvement."""
        self._memory.append({
            "prompt_id": prompt_id, "success": success,
            "quality_score": quality_score, "time": time.time()})

    def get_best_style(self) -> PromptStyle:
        """Performance dekh ke best style suggest karo."""
        style_scores: Dict[str, List[float]] = {}
        for entry in self._memory:
            if "style" in entry and "quality_score" in entry:
                style = entry["style"]
                style_scores.setdefault(style, []).append(entry["quality_score"])
        if not style_scores:
            return PromptStyle.DIRECT
        best_style = max(style_scores, key=lambda s: sum(style_scores[s]) / len(style_scores[s]))
        return PromptStyle(best_style)

    def list_templates(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._templates.values()]

    def get_stats(self) -> Dict[str, Any]:
        styles_used = {}
        for entry in self._memory:
            if "style" in entry:
                styles_used[entry["style"]] = styles_used.get(entry["style"], 0) + 1
        return {"total_prompts": len(self._memory), "styles_used": styles_used}
