"""LLMManager — Central AI model management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_config import LLMConfig
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_request import LLMRequest
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_response import LLMResponse
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_metrics import LLMMetrics
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_memory import LLMMemory
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cost_tracker import LLMCostTracker
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_health import LLMHealth
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_registry import LLMRegistry
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_fallback import LLMFallback
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_pool import LLMPool
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_rate_limit import LLMRateLimit
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cache import LLMCache
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_report import LLMReportGenerator


class LLMManager:
    """Central AI model management — the brain of the AI OS."""

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        self.config = config or LLMConfig()
        self.metrics = LLMMetrics()
        self.memory = LLMMemory()
        self.cost_tracker = LLMCostTracker(self.config.budget_limit)
        self.health = LLMHealth()
        self.registry = LLMRegistry()
        self.fallback = LLMFallback()
        self.pool = LLMPool()
        self.rate_limit = LLMRateLimit()
        self.cache = LLMCache()
        self.report_generator = LLMReportGenerator()
        self._is_running = False
        self._sessions: Dict[str, Any] = {}

    def start(self) -> bool:
        self._is_running = True
        return True

    def stop(self) -> bool:
        self._is_running = False
        return True

    def generate(self, prompt: str, model: str = "", provider: str = "",
                 temperature: float = None, max_tokens: int = None,
                 system_prompt: str = "") -> LLMResponse:
        model = model or self.config.default_model
        provider = provider or self.config.default_provider
        temperature = temperature if temperature is not None else self.config.default_temperature
        max_tokens = max_tokens or self.config.default_max_tokens

        request = LLMRequest(prompt, model, provider)
        request.temperature = temperature
        request.max_tokens = max_tokens
        request.system_prompt = system_prompt

        cache_key = f"{provider}:{model}:{prompt[:200]}"
        if self.config.enable_cache:
            cached = self.cache.get(prompt, model)
            if cached:
                response = LLMResponse(cached, model, provider)
                response.metadata["cached"] = True
                return response

        start = time.time()
        response = LLMResponse(self._simulate_response(prompt, model), model, provider)
        response.request_id = request.request_id
        response.latency_ms = (time.time() - start) * 1000
        response.usage = {"prompt_tokens": len(prompt.split()) * 2,
                          "completion_tokens": len(response.content.split()) * 2,
                          "total_tokens": len(prompt.split()) * 2 + len(response.content.split()) * 2}

        self.metrics.record_request(provider, model, response.total_tokens, 0.001,
                                    response.latency_ms, True)
        self.cost_tracker.record(provider, model, response.usage["prompt_tokens"],
                                  response.usage["completion_tokens"], 0.001)

        if self.config.enable_cache:
            self.cache.set(prompt, model, response.content)

        return response

    def generate_stream(self, prompt: str, model: str = "", on_chunk=None):
        response = self.generate(prompt, model)
        return response

    def chat(self, messages: List[Dict[str, str]], model: str = "",
             provider: str = "") -> LLMResponse:
        prompt = messages[-1]["content"] if messages else ""
        return self.generate(prompt, model, provider)

    def batch_generate(self, prompts: List[str], model: str = "",
                       provider: str = "") -> List[LLMResponse]:
        return [self.generate(p, model, provider) for p in prompts]

    def get_usage_report(self) -> Dict[str, Any]:
        return self.metrics.to_dict()

    def get_cost_report(self) -> Dict[str, Any]:
        return self.cost_tracker.get_stats()

    def get_health(self) -> Dict[str, Any]:
        return {"healthy": self._is_running, "health": self.health.get_stats(),
                "metrics": self.metrics.to_dict(), "cost": self.cost_tracker.get_stats()}

    def status(self) -> Dict[str, Any]:
        return {"running": self._is_running, "config": self.config.to_dict(),
                "metrics": self.metrics.to_dict(), "cache": self.cache.get_stats()}

    def _simulate_response(self, prompt: str, model: str) -> str:
        word_count = max(10, len(prompt.split()) * 3)
        return f"[{model}] Generated response for: {prompt[:80]}... ({word_count} words simulated)"
