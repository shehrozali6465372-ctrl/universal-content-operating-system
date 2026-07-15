"""Draft Manager — Central orchestrator for Draft Generator."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.draft_generator.llm_provider import BaseLLMProvider, MockLLMProvider, LLMResponse
from layers.layer04_writing.modules.draft_generator.prompt_builder import PromptBuilder, PromptSet
from layers.layer04_writing.modules.draft_generator.draft_validator import DraftValidator, DraftValidationResult
from layers.layer04_writing.modules.draft_generator.variant_generator import VariantGenerator
from layers.layer04_writing.modules.draft_generator.draft_memory import DraftMemory


class GeneratedDraft:
    """A complete generated draft with metadata."""
    __slots__ = ("draft_id", "plan_id", "topic", "text", "variant_type",
                 "prompt", "llm_response", "validation", "provider",
                 "tokens_used", "latency_ms", "metadata", "created_at")

    def __init__(self, topic: str = "", text: str = "") -> None:
        self.draft_id = f"draft_{int(time.time() * 1000) % 10000000}"
        self.plan_id = ""
        self.topic = topic
        self.text = text
        self.variant_type = "original"
        self.prompt: Optional[PromptSet] = None
        self.llm_response: Optional[LLMResponse] = None
        self.validation: Optional[DraftValidationResult] = None
        self.provider = ""
        self.tokens_used = 0
        self.latency_ms = 0.0
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "plan_id": self.plan_id,
            "topic": self.topic,
            "text": self.text,
            "variant_type": self.variant_type,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "latency_ms": round(self.latency_ms, 2),
            "validation": self.validation.to_dict() if self.validation else None,
            "created_at": self.created_at,
        }


class DraftManagerResult:
    """Result from the Draft Manager pipeline."""
    __slots__ = ("plan_id", "draft", "variants", "total_tokens",
                 "total_latency_ms", "timestamp")

    def __init__(self) -> None:
        self.plan_id = ""
        self.draft: Optional[GeneratedDraft] = None
        self.variants: List[GeneratedDraft] = []
        self.total_tokens = 0
        self.total_latency_ms = 0.0
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "draft": self.draft.to_dict() if self.draft else None,
            "variants_count": len(self.variants),
            "total_tokens": self.total_tokens,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "timestamp": self.timestamp,
        }


class DraftManager:
    """Central orchestrator for Draft Generation.

    Pipeline:
    Plan → Prompt → LLM → Validate → Store → Return
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        validator: Optional[DraftValidator] = None,
        variant_generator: Optional[VariantGenerator] = None,
        memory: Optional[DraftMemory] = None,
    ) -> None:
        self.provider = provider or MockLLMProvider()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.validator = validator or DraftValidator()
        self.variant_generator = variant_generator or VariantGenerator(self.prompt_builder)
        self.memory = memory or DraftMemory()
        self._draft_count = 0

    def generate(
        self,
        plan: WritingPlan,
        context: Optional[Dict[str, Any]] = None,
        validate: bool = True,
    ) -> DraftManagerResult:
        """Generate a draft from a WritingPlan."""
        start = time.time()
        result = DraftManagerResult()
        result.plan_id = plan.plan_id

        # 1. Build prompt
        prompt = self.prompt_builder.build(plan, context)

        # 2. Call LLM
        if not self.provider.is_configured():
            raise Exception("LLM provider not configured")

        llm_response = self.provider.generate(
            prompt=prompt.user_prompt,
            system_prompt=prompt.system_prompt,
        )

        # 3. Build draft
        draft = GeneratedDraft(topic=plan.topic, text=llm_response.text)
        draft.plan_id = plan.plan_id
        draft.prompt = prompt
        draft.llm_response = llm_response
        draft.provider = self.provider.provider_name
        draft.tokens_used = llm_response.tokens_used
        draft.latency_ms = llm_response.latency_ms

        # 4. Validate
        if validate:
            draft.validation = self.validator.validate(
                draft.text, length=plan.length, platform=plan.platform
            )

        # 5. Store in memory
        self.memory.store(
            plan_id=plan.plan_id, topic=plan.topic, text=draft.text,
            provider=draft.provider, model=llm_response.model,
            tokens=draft.tokens_used,
        )

        result.draft = draft
        result.total_tokens = draft.tokens_used
        result.total_latency_ms = (time.time() - start) * 1000
        self._draft_count += 1
        return result

    def generate_variants(
        self,
        plan: WritingPlan,
        variant_types: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DraftManagerResult:
        """Generate multiple variants from a plan."""
        start = time.time()
        result = DraftManagerResult()
        result.plan_id = plan.plan_id

        # Generate variants
        variants = self.variant_generator.generate_variants(plan, variant_types)

        generated: List[GeneratedDraft] = []
        total_tokens = 0

        for v in variants:
            if v.prompt_set:
                llm_resp = self.provider.generate(
                    prompt=v.prompt_set.user_prompt,
                    system_prompt=v.prompt_set.system_prompt,
                )
                draft = GeneratedDraft(topic=plan.topic, text=llm_resp.text)
                draft.plan_id = plan.plan_id
                draft.variant_type = v.variant_type
                draft.prompt = v.prompt_set
                draft.llm_response = llm_resp
                draft.provider = self.provider.provider_name
                draft.tokens_used = llm_resp.tokens_used
                draft.validation = self.validator.validate(draft.text, length=plan.length)
                total_tokens += draft.tokens_used

                self.memory.store(
                    plan_id=plan.plan_id, topic=plan.topic, text=draft.text,
                    variant_type=v.variant_type, provider=draft.provider,
                    tokens=draft.tokens_used,
                )
                generated.append(draft)

        result.variants = generated
        result.draft = generated[0] if generated else None
        result.total_tokens = total_tokens
        result.total_latency_ms = (time.time() - start) * 1000
        self._draft_count += len(generated)
        return result

    def get_history(self, topic: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Get draft history."""
        if topic:
            return [r.to_dict() for r in self.memory.get_by_topic(topic, limit)]
        return [r.to_dict() for r in self.memory.get_recent(limit)]

    @property
    def draft_count(self) -> int:
        return self._draft_count
