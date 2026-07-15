"""Writing Orchestrator — One input → multiple platform outputs."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager
from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.draft_generator.draft_manager import DraftManager
from layers.layer04_writing.modules.draft_generator.llm_provider import BaseLLMProvider, MockLLMProvider
from layers.layer04_writing.modules.caption_engine.caption_engine import CaptionEngine
from layers.layer04_writing.modules.hashtag_engine.hashtag_engine import HashtagEngine
from layers.layer04_writing.modules.tone_adapter.tone_adapter import ToneAdapter
from layers.layer04_writing.modules.hook_engine.hook_engine import HookEngine
from layers.layer04_writing.modules.cta_engine.cta_engine import CTAGenerator
from layers.layer04_writing.modules.content_optimizer.content_optimizer import ContentOptimizer
from layers.layer04_writing.modules.writing_memory.writing_memory import WritingMemory


class PlatformOutput:
    """Output for a single platform."""
    __slots__ = ("platform", "caption", "hashtags", "hook", "cta",
                 "adapted_tone", "optimized_text", "metadata")

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.caption = ""
        self.hashtags: List[str] = []
        self.hook = ""
        self.cta = ""
        self.adapted_tone = ""
        self.optimized_text = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "caption": self.caption,
            "hashtags": self.hashtags,
            "hook": self.hook,
            "cta": self.cta,
            "adapted_tone": self.adapted_tone,
            "optimized_length": len(self.optimized_text),
        }


class OrchestratorResult:
    """Result from the Writing Orchestrator."""
    __slots__ = ("topic", "platforms", "outputs", "plan", "draft",
                 "total_tokens", "pipeline_time_ms", "metadata")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.platforms: List[str] = []
        self.outputs: List[PlatformOutput] = []
        self.plan: Optional[WritingPlan] = None
        self.draft = ""
        self.total_tokens = 0
        self.pipeline_time_ms = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "platforms": self.platforms,
            "outputs_count": len(self.outputs),
            "outputs": [o.to_dict() for o in self.outputs],
            "draft_preview": self.draft[:100] + "..." if len(self.draft) > 100 else self.draft,
            "total_tokens": self.total_tokens,
            "pipeline_time_ms": round(self.pipeline_time_ms, 2),
        }


class WritingOrchestrator:
    """One input → multiple optimized platform outputs.

    Pipeline:
    Topic → Plan → Draft → Caption → Hashtags → Hook → CTA
    → Tone Adapt → Optimize → Store → Return
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        self.planner = PlannerManager()
        self.draft_manager = DraftManager(provider=provider or MockLLMProvider())
        self.caption_engine = CaptionEngine()
        self.hashtag_engine = HashtagEngine()
        self.hook_engine = HookEngine()
        self.cta_engine = CTAGenerator()
        self.tone_adapter = ToneAdapter()
        self.optimizer = ContentOptimizer()
        self.memory = WritingMemory()
        self._run_count = 0

    def run(
        self,
        topic: str,
        platforms: Optional[List[str]] = None,
        goal: str = "educate",
        audience: str = "general",
        language: str = "english",
    ) -> OrchestratorResult:
        """Full pipeline: one topic → multiple platform outputs."""
        start = time.time()
        result = OrchestratorResult(topic=topic)
        target_platforms = platforms or ["facebook", "instagram", "twitter", "linkedin"]

        # 1. Plan
        plan_result = self.planner.create_plan(
            topic=topic, user_goal=goal, audience_hint=audience
        )
        result.plan = plan_result.plan

        # 2. Generate draft
        draft_result = self.draft_manager.generate(plan_result.plan)
        result.draft = draft_result.draft.text if draft_result.draft else ""
        result.total_tokens = draft_result.total_tokens

        # 3. Generate hook
        hook_result = self.hook_engine.generate(topic, goal=goal, platform="facebook")

        # 4. For each platform, optimize
        for platform in target_platforms:
            po = PlatformOutput(platform=platform)

            # Caption
            caption = self.caption_engine.generate(result.draft, platform=platform)
            po.caption = caption.caption

            # Hashtags
            hashtags = self.hashtag_engine.generate(result.draft, platform=platform)
            po.hashtags = hashtags.hashtags

            # Hook
            po.hook = hook_result.hook

            # CTA
            cta = self.cta_engine.generate(platform=platform, goal=goal)
            po.cta = cta.cta_text

            # Tone Adapt
            if platform != "facebook":
                adapted = self.tone_adapter.adapt(result.draft, target_platform=platform)
                po.adapted_tone = adapted.target_tone
                po.optimized_text = adapted.adapted_text
            else:
                po.adapted_tone = "conversational"
                po.optimized_text = result.draft

            # Optimize
            optimized = self.optimizer.optimize(po.optimized_text, platform=platform)
            po.optimized_text = optimized.optimized_text

            result.outputs.append(po)

            # Store in memory
            self.memory.store_draft(
                platform=platform, topic=topic, text=po.optimized_text,
                tone=po.adapted_tone, tokens=draft_result.total_tokens,
            )

        result.platforms = target_platforms
        result.pipeline_time_ms = (time.time() - start) * 1000
        self._run_count += 1
        return result

    def get_history(self, platform: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        if platform:
            return [r.to_dict() for r in self.memory.get_by_platform(platform, limit)]
        return [r.to_dict() for r in self.memory.get_recent(limit)]

    @property
    def run_count(self) -> int:
        return self._run_count
