"""CotEngine — Chain-of-Thought prompting for complex reasoning."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class CotEngine:
    """Chain-of-Thought prompting engine for complex reasoning tasks."""

    STRATEGIES = ("basic", "structured", "tree", "reflexion", "self_consistency")

    def __init__(self, strategy: str = "basic") -> None:
        self.strategy = strategy if strategy in self.STRATEGIES else "basic"
        self._history: List[Dict[str, Any]] = []

    def generate_prompt(self, question: str, context: str = "",
                        steps: Optional[List[str]] = None) -> str:
        if self.strategy == "basic":
            return self._basic_cot(question)
        elif self.strategy == "structured":
            return self._structured_cot(question, context)
        elif self.strategy == "tree":
            return self._tree_cot(question)
        elif self.strategy == "reflexion":
            return self._reflexion_cot(question)
        elif self.strategy == "self_consistency":
            return self._self_consistency_cot(question)
        return self._basic_cot(question)

    def analyze_steps(self, reasoning: str) -> Dict[str, Any]:
        lines = [l.strip() for l in reasoning.split("\n") if l.strip()]
        step_lines = [l for l in lines if any(w in l.lower() for w in ["step", "therefore", "thus", "because", "so"])]
        conclusion = ""
        for l in reversed(lines):
            if any(w in l.lower() for w in ["therefore", "conclusion", "final", "answer", "result"]):
                conclusion = l
                break
        return {
            "total_lines": len(lines),
            "step_indicators": len(step_lines),
            "has_conclusion": bool(conclusion),
            "conclusion": conclusion,
        }

    @staticmethod
    def _basic_cot(question: str) -> str:
        return f"{question}\n\nLet's think step by step:\nStep 1:"

    @staticmethod
    def _structured_cot(question: str, context: str = "") -> str:
        parts = [f"Question: {question}"]
        if context:
            parts.append(f"Context: {context}")
        parts.extend(["\nReasoning:", "Step 1: Understand the problem", "Step 2: Identify key information",
                       "Step 3: Apply reasoning", "Step 4: Form conclusion", "Answer:"])
        return "\n".join(parts)

    @staticmethod
    def _tree_cot(question: str) -> str:
        return (f"{question}\n\n"
                "Consider multiple approaches:\n"
                "Approach A:\n  -\nApproach B:\n  -\n"
                "Compare approaches and select the best:\nAnswer:")

    @staticmethod
    def _reflexion_cot(question: str) -> str:
        return (f"{question}\n\n"
                "Initial attempt:\n[reasoning]\n\n"
                "Reflection — what might be wrong:\n[reflection]\n\n"
                "Improved reasoning:\n[improved]\n\nFinal answer:")

    @staticmethod
    def _self_consistency_cot(question: str) -> str:
        return (f"{question}\n\n"
                "Reasoning path 1:\n  \nReasoning path 2:\n  \n"
                "Reasoning path 3:\n  \nMost consistent answer:")

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
