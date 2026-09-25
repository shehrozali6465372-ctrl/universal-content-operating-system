"""LLMManager — Central AI model management."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_config import (
    LLMConfig,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_request import (
    LLMRequest,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_response import (
    LLMResponse,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_metrics import (
    LLMMetrics,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_memory import (
    LLMMemory,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cost_tracker import (
    LLMCostTracker,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_health import (
    LLMHealth,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_registry import (
    LLMRegistry,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_fallback import (
    LLMFallback,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_pool import (
    LLMPool,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_rate_limit import (
    LLMRateLimit,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cache import (
    LLMCache,
)
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_report import (
    LLMReportGenerator,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderResponse


class LLMManager:
    """Central AI model management — the brain of the AI OS."""

    def __init__(
        self, config: Optional[LLMConfig] = None, generator: Any = None
    ) -> None:
        self.config = config or LLMConfig()
        self._generator = generator
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

    def generate(
        self,
        prompt: str,
        model: str = "",
        provider: str = "",
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = "",
    ) -> LLMResponse:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        model = model or self.config.default_model
        provider = provider or self.config.default_provider
        temperature = (
            temperature
            if temperature is not None
            else self.config.default_temperature
        )
        max_tokens = (
            max_tokens
            if max_tokens is not None
            else self.config.default_max_tokens
        )
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        request = LLMRequest(prompt, model, provider)
        request.temperature = temperature
        request.max_tokens = max_tokens
        request.system_prompt = system_prompt

        if self.config.enable_cache:
            cached = self.cache.get(
                prompt,
                model,
                provider,
                system_prompt,
                temperature,
                max_tokens,
            )
            if cached:
                response = LLMResponse(cached, model, provider)
                response.metadata["cached"] = True
                return response

        start = time.time()
        if self._generator is None:
            if os.getenv("UCOS_ENV", "").strip().lower() == "production":
                raise RuntimeError(
                    "LLMManager has no production generator; "
                    "refusing simulated AI output"
                )
            generated = (
                f"[development-only simulated response for {provider}/{model}]"
            )
        else:
            generated = self._generator(
                prompt=prompt,
                model=model,
                provider=provider,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            if not isinstance(generated, (str, ProviderResponse, LLMResponse)):
                raise RuntimeError("AI generator returned an unsupported response type")

        if isinstance(generated, ProviderResponse):
            response = LLMResponse(generated.content, generated.model, generated.provider)
            response.request_id = generated.request_id or request.request_id
            response.finish_reason = generated.finish_reason
            response.usage = dict(generated.usage)
            response.latency_ms = generated.latency_ms or (time.time() - start) * 1000
            response.metadata["usage_estimated"] = False
            response.metadata["cost_estimated"] = False
        elif isinstance(generated, LLMResponse):
            response = generated
            response.request_id = response.request_id or request.request_id
            response.latency_ms = response.latency_ms or (time.time() - start) * 1000
        else:
            response = LLMResponse(generated, model, provider)
            response.request_id = request.request_id
            response.latency_ms = (time.time() - start) * 1000
            response.usage = {
                "prompt_tokens": len(prompt.split()) * 2,
                "completion_tokens": len(response.content.split()) * 2,
                "total_tokens": (
                    len(prompt.split()) * 2 + len(response.content.split()) * 2
                ),
            }
            response.metadata["usage_estimated"] = True
            response.metadata["cost_estimated"] = True

        self.metrics.record_request(
            provider, model, response.total_tokens, 0.001,
            response.latency_ms, True
        )
        self.cost_tracker.record(
            provider,
            model,
            response.usage["prompt_tokens"],
            response.usage["completion_tokens"],
            0.001,
        )

        if self.config.enable_cache:
            self.cache.set(
                prompt,
                model,
                response.content,
                provider,
                system_prompt,
                temperature,
                max_tokens,
            )

        return response

    def generate_stream(self, prompt: str, model: str = "", on_chunk=None):
        if not self.config.enable_streaming:
            raise RuntimeError(
                "streaming is disabled; enable_streaming must be true"
            )
        raise NotImplementedError(
            "LLMManager streaming requires a provider-native streaming adapter"
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        provider: str = "",
    ) -> LLMResponse:
        if not messages:
            raise ValueError("messages must not be empty")
        system_prompt = ""
        conversation: List[Dict[str, str]] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if not isinstance(role, str) or not isinstance(content, str):
                raise ValueError("each message requires string role and content")
            if role == "system":
                system_prompt = content
            else:
                conversation.append({"role": role, "content": content})
        if self._generator is None:
            return self.generate(
                conversation[-1]["content"] if conversation else "",
                model,
                provider,
                system_prompt=system_prompt,
            )
        generated = self._generator(
            messages=conversation,
            model=model or self.config.default_model,
            provider=provider or self.config.default_provider,
            system_prompt=system_prompt,
            temperature=self.config.default_temperature,
            max_tokens=self.config.default_max_tokens,
        )
        if not isinstance(generated, str) or not generated.strip():
            raise RuntimeError(
                "AI generator returned empty or non-text chat output"
            )
        response = LLMResponse(
            generated,
            model or self.config.default_model,
            provider or self.config.default_provider,
        )
        response.metadata["usage_estimated"] = True
        response.metadata["cost_estimated"] = True
        return response

    def batch_generate(
        self, prompts: List[str], model: str = "", provider: str = ""
    ) -> List[LLMResponse]:
        return [self.generate(p, model, provider) for p in prompts]

    def get_usage_report(self) -> Dict[str, Any]:
        return self.metrics.to_dict()

    def get_cost_report(self) -> Dict[str, Any]:
        return self.cost_tracker.get_stats()

    def get_health(self) -> Dict[str, Any]:
        return {
            "healthy": self._is_running,
            "health": self.health.get_stats(),
            "metrics": self.metrics.to_dict(),
            "cost": self.cost_tracker.get_stats(),
        }

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._is_running,
            "config": self.config.to_dict(),
            "metrics": self.metrics.to_dict(),
            "cache": self.cache.get_stats(),
        }
