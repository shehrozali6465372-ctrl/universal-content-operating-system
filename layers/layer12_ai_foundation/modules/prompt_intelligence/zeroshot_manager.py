"""ZeroShotManager — generate zero-shot prompts without examples."""
from __future__ import annotations

from typing import Any, Dict, List


class ZeroShotManager:
    """Generate zero-shot prompts that don't require examples."""

    TASK_DESCRIPTIONS: Dict[str, str] = {
        "classification": "Classify the input into the correct category.",
        "summarization": "Summarize the input concisely.",
        "translation": "Translate the input to the target language.",
        "sentiment": "Determine the sentiment of the input.",
        "extraction": "Extract the requested information from the input.",
        "generation": "Generate content based on the instructions.",
        "rewriting": "Rewrite the input according to the given requirements.",
        "question": "Answer the question based on your knowledge.",
    }

    def __init__(self) -> None:
        self._custom_tasks: Dict[str, str] = {}

    def generate_prompt(self, task: str, input_text: str,
                        extra_instructions: str = "") -> str:
        desc = self._custom_tasks.get(task, self.TASK_DESCRIPTIONS.get(task, f"Perform {task}"))
        parts = [f"Task: {desc}"]
        if extra_instructions:
            parts.append(f"Instructions: {extra_instructions}")
        parts.append(f"Input: {input_text}")
        parts.append("Output:")
        return "\n".join(parts)

    def register_task(self, task: str, description: str) -> None:
        self._custom_tasks[task] = description

    def list_tasks(self) -> List[str]:
        return list(set(list(self.TASK_DESCRIPTIONS.keys()) + list(self._custom_tasks.keys())))

    def to_dict(self) -> Dict[str, Any]:
        return {"builtin_tasks": list(self.TASK_DESCRIPTIONS.keys()),
                "custom_tasks": list(self._custom_tasks.keys())}
