"""PromptOrchestrator — full prompt intelligence pipeline."""
from __future__ import annotations

import time
from typing import Any, Dict

from .prompt_optimizer import PromptOptimizer
from .prompt_memory import PromptMemory
from .prompt_library import PromptLibrary
from .prompt_builder import PromptBuilder
from .fewshot_manager import FewShotManager
from .zeroshot_manager import ZeroShotManager
from .cot_engine import CotEngine
from .system_prompt_manager import SystemPromptManager
from .dynamic_prompt import DynamicPrompt
from .prompt_validator import PromptValidator
from .prompt_metrics import PromptMetrics
from .prompt_events import PromptEvents
from .prompt_health import PromptHealth
from .prompt_cache import PromptCache


class PromptOrchestrator:
    """Full prompt intelligence pipeline orchestrator."""

    def __init__(self) -> None:
        self.optimizer = PromptOptimizer()
        self.memory = PromptMemory()
        self.library = PromptLibrary()
        self.builder = PromptBuilder()
        self.fewshot = FewShotManager()
        self.zeroshot = ZeroShotManager()
        self.cot = CotEngine()
        self.system = SystemPromptManager()
        self.dynamic = DynamicPrompt()
        self.validator = PromptValidator()
        self.metrics = PromptMetrics()
        self.events = PromptEvents()
        self.health = PromptHealth()
        self.cache = PromptCache()
        self._is_running = False

    def start(self) -> bool:
        self._is_running = True
        self.events.publish("started")
        return True

    def stop(self) -> bool:
        self._is_running = False
        self.events.publish("stopped")
        return True

    def generate_prompt(self, task: str, input_text: str,
                        role: str = "assistant",
                        use_cot: bool = False,
                        use_fewshot: bool = False) -> Dict[str, Any]:
        start = time.time()

        # Build the prompt
        system = self.system.get_prompt(role)
        zero_shot = self.zeroshot.generate_prompt(task, input_text)

        parts = {"system": system, "prompt": zero_shot}

        if use_cot:
            cot_prompt = self.cot.generate_prompt(input_text)
            parts["cot_prompt"] = cot_prompt

        if use_fewshot:
            examples = self.fewshot.get_for_prompt(task, limit=3)
            parts["fewshot"] = [{"input": e.input_text, "output": e.output_text} for e in examples]

        # Optimize
        optimized = self.optimizer.optimize(parts["prompt"], task)
        parts["optimized_prompt"] = optimized.optimized

        # Validate
        validation = self.validator.validate(parts["optimized_prompt"])
        parts["validation"] = validation

        elapsed = (time.time() - start) * 1000
        self.metrics.record_prompt(task, elapsed)
        self.events.publish("prompt_generated", {"task": task, "latency_ms": elapsed})

        return parts

    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()
