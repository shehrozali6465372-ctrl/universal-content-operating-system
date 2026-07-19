"""PipelineWiring — End-to-End Content Pipeline

Chain:
    Topic → Research (L2) → Intelligence (L3) → Writing Plan (L4)
        → AI Generation (L12/Gemini) → Image Plan (L5)
        → Quality Check (L6) → Publish Package (L7)
        → Analytics Record (L8) → Learning Memory (L9)
"""
from __future__ import annotations
import os
import time
import traceback
from typing import Any, Dict, List, Optional


# ── GitHub Secret names (key 2 & 3 have no underscores) ──
_GEMINI_KEYS = [
    ("GEMINI_API_KEY_1", "GEMINI_API_KEY_1"),
    ("GEMINI_API_KEY_2", "GEMINIAPIKEY2"),
    ("GEMINI_API_KEY_3", "GEMINIAPIKEY3"),
]


# ── Pipeline Data Objects ──

class ContentRequest:
    """What the user wants to create."""
    __slots__ = ("topic", "platform", "tone", "style", "include_image",
                 "max_length", "metadata")

    def __init__(self, topic: str, platform: str = "facebook",
                 tone: str = "professional", style: str = "educational",
                 include_image: bool = True, max_length: int = 1000) -> None:
        self.topic = topic
        self.platform = platform
        self.tone = tone
        self.style = style
        self.include_image = include_image
        self.max_length = max_length
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"topic": self.topic, "platform": self.platform,
                "tone": self.tone, "style": self.style,
                "include_image": self.include_image}


class PipelineStepResult:
    """Result of a single pipeline step."""
    __slots__ = ("layer", "status", "data", "error", "duration_ms")

    def __init__(self, layer: str) -> None:
        self.layer = layer
        self.status = "pending"
        self.data: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer, "status": self.status,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
            "data_keys": list(self.data.keys()),
        }


class ContentResponse:
    """Final output of the full pipeline."""
    __slots__ = ("request", "steps", "text", "image_prompt",
                 "quality_score", "quality_report", "publish_package",
                 "analytics", "learning_entries", "total_duration_ms", "stats")

    def __init__(self, request: ContentRequest) -> None:
        self.request = request
        self.steps: List[PipelineStepResult] = []
        self.text: str = ""
        self.image_prompt: str = ""
        self.quality_score: float = 0.0
        self.quality_report: Optional[Dict[str, Any]] = None
        self.publish_package: Optional[Dict[str, Any]] = None
        self.analytics: Optional[Dict[str, Any]] = None
        self.learning_entries: List[Dict[str, Any]] = []
        self.total_duration_ms: float = 0.0
        self.stats: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.request.topic,
            "platform": self.request.platform,
            "content_length": len(self.text),
            "quality_score": self.quality_score,
            "image_prompt": self.image_prompt[:200] if self.image_prompt else "",
            "publish_ready": self.publish_package is not None,
            "steps_completed": len([s for s in self.steps if s.status == "success"]),
            "steps_failed": len([s for s in self.steps if s.status == "error"]),
            "steps_skipped": len([s for s in self.steps if s.status == "skipped"]),
            "total_duration_ms": round(self.total_duration_ms, 1),
            "steps": [s.to_dict() for s in self.steps],
        }


# ── Pipeline Logger ──

class PipelineLogger:
    """Simple structured logger for pipeline events."""

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def log(self, layer: str, event: str, data: Optional[Dict] = None) -> None:
        entry = {"time": time.time(), "layer": layer, "event": event}
        if data:
            entry["data"] = data
        self.events.append(entry)
        icon = "✅" if "success" in event else ("❌" if "error" in event else "🔄")
        print(f"  {icon} [{layer}] {event}")

    def summary(self) -> List[Dict[str, Any]]:
        return self.events


# ── Main Pipeline ──

class PipelineWiring:
    """End-to-end content pipeline wiring all layers together."""

    def __init__(self) -> None:
        self._logger = PipelineLogger()
        self._key_manager = None
        self._gemini = None
        self._prompt_builder = None
        self._init_ai()

    def _init_ai(self) -> None:
        """Initialize Gemini AI engine."""
        try:
            from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
            from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
            from layers.layer12_ai_foundation.modules.model_router.prompt_builder import PromptBuilder

            self._key_manager = KeyManager()
            for idx, (env_name, secret_name) in enumerate(_GEMINI_KEYS, 1):
                key = os.environ.get(env_name) or os.environ.get(secret_name)
                if key:
                    self._key_manager.register_key(f"k{idx}", key, "gemini")

            self._gemini = GeminiProvider(self._key_manager)
            self._prompt_builder = PromptBuilder()
            self._logger.log("L12-AI", "Gemini initialized",
                             {"keys": self._key_manager.get_stats().get("total_keys", 0)})
        except Exception as exc:
            self._logger.log("L12-AI", f"init error: {exc}")

    def _run_step(self, layer: str, fn, response: ContentResponse,
                  required_from: Optional[str] = None) -> bool:
        """Run a pipeline step with error handling and timing."""
        step = PipelineStepResult(layer)
        response.steps.append(step)

        if required_from:
            prev = next((s for s in response.steps if s.layer == required_from), None)
            if prev and prev.status != "success":
                step.status = "skipped"
                step.error = f"Skipped: {required_from} did not succeed"
                self._logger.log(layer, "skipped", {"reason": step.error})
                return False

        start = time.time()
        try:
            step.data = fn() or {}
            step.status = "success"
            step.duration_ms = (time.time() - start) * 1000
            self._logger.log(layer, "success",
                             {"duration_ms": round(step.duration_ms, 1),
                              "keys": list(step.data.keys())[:5]})
            return True
        except Exception as exc:
            step.status = "error"
            step.error = str(exc)
            step.duration_ms = (time.time() - start) * 1000
            self._logger.log(layer, f"error: {exc}")
            return False

    # ── Pipeline Steps ──

    def _step_research(self, req: ContentRequest, response: ContentResponse,
                       ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L2: Research — add topic to intelligence system."""
        from layers.layer02_research.modules.topic_intelligence.topic_intel_manager import TopicIntelManager
        manager = TopicIntelManager()
        topic_entry = manager.add_topic(
            name=req.topic,
            niche=req.platform,
            category=req.style,
            confidence=0.5,
        )
        ctx["topic_id"] = topic_entry.topic_id if hasattr(topic_entry, "topic_id") else ""
        return {"topic_id": ctx["topic_id"], "topic_name": req.topic}

    def _step_intelligence(self, req: ContentRequest, response: ContentResponse,
                           ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L3: Intelligence — analyze topic for insights."""
        from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
        analyzer = ContentAnalyzer()
        understanding = analyzer.analyze(req.topic, domain=req.platform)
        ctx["keywords"] = understanding.keywords if hasattr(understanding, "keywords") else []
        ctx["entities"] = understanding.entities if hasattr(understanding, "entities") else []
        ctx["intent"] = understanding.intent if hasattr(understanding, "intent") else "informational"
        return {"keywords": ctx["keywords"], "intent": ctx["intent"]}

    def _step_writing_plan(self, req: ContentRequest, response: ContentResponse,
                           ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L4: Writing — create content plan."""
        from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager
        planner = PlannerManager()
        result = planner.create_plan(
            topic=req.topic,
            platform=req.platform,
            user_goal="educate",
            audience_hint="general",
            tone_override=req.tone,
        )
        plan = result.plan if hasattr(result, "plan") else None
        if plan:
            ctx["writing_plan"] = plan
            structure = plan.structure if hasattr(plan, "structure") else {}
            return {"plan_id": getattr(plan, "plan_id", ""), "structure": structure}
        return {"plan_id": "", "note": "Plan created (no structure details)"}

    def _step_ai_generate(self, req: ContentRequest, response: ContentResponse,
                          ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L12: AI Generation — use Gemini to write content."""
        if not self._gemini:
            raise RuntimeError("Gemini not initialized — no API keys configured")

        keywords_str = ", ".join(str(k) for k in ctx.get("keywords", [])[:5])
        prompt_text = (
            f"Write a detailed, engaging {req.tone} social media post for {req.platform}.\n"
            f"Topic: {req.topic}\n"
            f"Key points to include: {keywords_str}\n"
            f"Style: {req.style}\n"
            f"Length: approximately {req.max_length} words.\n"
            f"Make it informative, engaging, and shareable. "
            f"Include a strong hook, valuable insights, and a call-to-action."
        )

        prompt = self._prompt_builder.build(
            prompt_text,
            style=__import__(
                "layers.layer12_ai_foundation.modules.model_router.prompt_builder",
                fromlist=["PromptStyle"]
            ).PromptStyle.CHAIN_OF_THOUGHT,
            context={"platform": req.platform, "tone": req.tone}
        )
        user_msg = next(
            (m["content"] for m in prompt["messages"] if m["role"] == "user"),
            prompt_text
        )

        result = self._gemini.generate(user_msg)
        content = result.get("content", "")
        response.text = content
        ctx["ai_model"] = result.get("model", "gemini")
        ctx["content_length"] = len(content)
        return {"content_length": len(content), "model": ctx["ai_model"]}

    def _step_image_plan(self, req: ContentRequest, response: ContentResponse,
                         ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L5: Image — plan image generation."""
        if not req.include_image:
            return {"skipped": True, "reason": "include_image=False"}

        from layers.layer05_image.modules.image_planner.image_planner import ImagePlanner
        planner = ImagePlanner()
        plans = planner.plan(req.topic, platform=req.platform, image_type="photo", count=1)
        plan = plans[0] if plans else None
        img_type = plan.image_type if plan and hasattr(plan, "image_type") else "photo"
        ctx["image_type"] = img_type

        img_prompt_text = (
            f"Create a {img_type} image for a {req.platform} post about '{req.topic}'. "
            f"Style: {req.tone}, {req.style}. High quality, professional, engaging."
        )
        response.image_prompt = img_prompt_text
        return {"image_type": img_type, "prompt": img_prompt_text[:150]}

    def _step_quality(self, req: ContentRequest, response: ContentResponse,
                      ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L6: Quality — analyze content quality."""
        if not response.text:
            return {"skipped": True, "reason": "No content to analyze"}

        from layers.layer06_quality.modules.content_quality_analyzer.quality_analyzer import ContentQualityAnalyzer
        analyzer = ContentQualityAnalyzer()
        report = analyzer.analyze(response.text, platform=req.platform)
        score = report.overall_score if hasattr(report, "overall_score") else 5.0
        response.quality_score = score
        response.quality_report = report.to_dict() if hasattr(report, "to_dict") else {}
        return {"quality_score": score, "report": response.quality_report}

    def _step_publish_package(self, req: ContentRequest, response: ContentResponse,
                              ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L7: Publishing — create publish package."""
        if not response.text:
            return {"skipped": True, "reason": "No content to publish"}

        from layers.layer07_publishing.modules.publishing_planner.planner_engine import PlannerEngine
        engine = PlannerEngine()
        plan = engine.create_plan(
            content_id=f"pipe-{int(time.time())}",
            content_type="post",
            preferred_platforms=[req.platform],
            schedule_mode="immediate",
        )
        package = plan.to_dict() if hasattr(plan, "to_dict") else {"status": "prepared"}
        response.publish_package = package
        return {"publish_package": package}

    def _step_analytics(self, req: ContentRequest, response: ContentResponse,
                        ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L8: Analytics — record pipeline metrics."""
        from layers.layer08_analytics.modules.analytics_orchestrator.orchestrator import AnalyticsOrchestrator
        orch = AnalyticsOrchestrator()
        metadata = {
            "topic": req.topic,
            "platform": req.platform,
            "content_length": len(response.text),
            "quality_score": response.quality_score,
            "pipeline_steps": len(response.steps),
            "ai_model": ctx.get("ai_model", "unknown"),
        }
        result = orch.run_pipeline(collect=True, calculate=True, detect_trends=True)
        analytics_data = result.to_dict() if hasattr(result, "to_dict") else {}
        response.analytics = analytics_data
        return {"analytics_recorded": True, "data": analytics_data}

    def _step_learning(self, req: ContentRequest, response: ContentResponse,
                       ctx: Dict[str, Any]) -> Dict[str, Any]:
        """L9: Learning — store lesson in memory."""
        from layers.layer09_learning.modules.learning_engine.learning_memory import LearningMemory
        from layers.layer09_learning.modules.learning_engine.lesson_generator import Lesson

        memory = LearningMemory()
        lesson = Lesson(
            lesson_type="pipeline_execution",
            title=f"Generated content for '{req.topic}' on {req.platform}",
        )
        lesson.description = f"Quality: {response.quality_score}/10, {len(response.text)} chars"
        lesson.confidence = min(1.0, response.quality_score / 10.0)
        lesson.platform = req.platform
        lesson.category = req.tone

        entry = memory.store_lesson(lesson)
        entry_data = entry.to_dict() if hasattr(entry, "to_dict") else {"id": "stored"}
        response.learning_entries.append(entry_data)
        return {"lesson_stored": True, "entry": entry_data}

    # ── Main Execute ──

    def execute(self, request: ContentRequest) -> ContentResponse:
        """Run the full end-to-end pipeline."""
        pipeline_start = time.time()
        response = ContentResponse(request)
        ctx: Dict[str, Any] = {}
        self._logger = PipelineLogger()

        print(f"\n{'=' * 60}")
        print(f"🚀 PIPELINE: \"{request.topic}\" → {request.platform}")
        print(f"{'=' * 60}")

        # Step chain: each step depends on the previous
        steps = [
            ("L2-Research",    lambda: self._step_research(request, response, ctx)),
            ("L3-Intelligence", lambda: self._step_intelligence(request, response, ctx)),
            ("L4-Writing",     lambda: self._step_writing_plan(request, response, ctx)),
            ("L12-AI",         lambda: self._step_ai_generate(request, response, ctx)),
            ("L5-Image",       lambda: self._step_image_plan(request, response, ctx)),
            ("L6-Quality",     lambda: self._step_quality(request, response, ctx)),
            ("L7-Publish",     lambda: self._step_publish_package(request, response, ctx)),
            ("L8-Analytics",   lambda: self._step_analytics(request, response, ctx)),
            ("L9-Learning",    lambda: self._step_learning(request, response, ctx)),
        ]

        required_from = None
        for layer_name, step_fn in steps:
            ok = self._run_step(layer_name, step_fn, response, required_from)
            if not ok and required_from is None:
                # First two steps are required; after that, skip gracefully
                if layer_name == "L12-AI":
                    required_from = layer_name

        response.total_duration_ms = (time.time() - pipeline_start) * 1000
        response.stats = {"execution_time_ms": round(response.total_duration_ms, 1)}

        # Summary
        success = len([s for s in response.steps if s.status == "success"])
        failed = len([s for s in response.steps if s.status == "error"])
        skipped = len([s for s in response.steps if s.status == "skipped"])
        print(f"\n{'=' * 60}")
        print(f"✅ PIPELINE COMPLETE: {success} success, {failed} error, {skipped} skipped")
        print(f"   Duration: {round(response.total_duration_ms, 1)}ms")
        print(f"   Content: {len(response.text)} chars | Quality: {response.quality_score}/10")
        print(f"{'=' * 60}\n")

        return response

    def status(self) -> Dict[str, Any]:
        """Return system status."""
        keys_info = {}
        if self._key_manager:
            keys_info = self._key_manager.get_stats()
        return {
            "pipeline": "active",
            "ai_engine": "gemini" if self._gemini else "unavailable",
            "api_keys_configured": keys_info.get("total_keys", 0),
            "healthy_keys": keys_info.get("healthy", 0),
        }
