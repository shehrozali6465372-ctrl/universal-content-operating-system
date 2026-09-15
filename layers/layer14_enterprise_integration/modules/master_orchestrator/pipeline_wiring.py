"""Canonical UCOS content pipeline.

Research -> intelligence -> writing -> AI -> image -> quality -> publishing
-> analytics -> learning -> persistence. External publishing and analytics are
reported only when a real adapter and real credentials are available.
"""
from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, List, Optional

_GEMINI_KEYS = (("GEMINI_API_KEY_1", "GEMINI_API_KEY_1"),
                ("GEMINI_API_KEY_2", "GEMINIAPIKEY2"),
                ("GEMINI_API_KEY_3", "GEMINIAPIKEY3"))


class ContentRequest:
    __slots__ = ("topic", "platform", "tone", "style", "include_image", "max_length", "metadata")

    def __init__(self, topic: str, platform: str = "facebook", tone: str = "professional",
                 style: str = "educational", include_image: bool = True, max_length: int = 1000) -> None:
        self.topic = topic.strip()
        self.platform = platform.strip().lower()
        self.tone = tone
        self.style = style
        self.include_image = include_image
        self.max_length = max_length
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"topic": self.topic, "platform": self.platform, "tone": self.tone,
                "style": self.style, "include_image": self.include_image,
                "max_length": self.max_length, "metadata": self.metadata}


class PipelineStepResult:
    __slots__ = ("layer", "status", "data", "error", "duration_ms")

    def __init__(self, layer: str) -> None:
        self.layer = layer
        self.status = "pending"
        self.data: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.duration_ms = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"layer": self.layer, "status": self.status, "duration_ms": round(self.duration_ms, 1),
                "error": self.error, "data_keys": list(self.data.keys())}


class ContentResponse:
    __slots__ = ("request", "steps", "text", "image_prompt", "image_url", "quality_score",
                 "quality_report", "publish_package", "publish_result", "analytics",
                 "learning_entries", "total_duration_ms", "stats")

    def __init__(self, request: ContentRequest) -> None:
        self.request = request
        self.steps: List[PipelineStepResult] = []
        self.text = ""
        self.image_prompt = ""
        self.image_url = ""
        self.quality_score = 0.0
        self.quality_report: Optional[Dict[str, Any]] = None
        self.publish_package: Optional[Dict[str, Any]] = None
        self.publish_result: Optional[Dict[str, Any]] = None
        self.analytics: Optional[Dict[str, Any]] = None
        self.learning_entries: List[Dict[str, Any]] = []
        self.total_duration_ms = 0.0
        self.stats: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        published = bool(self.publish_result and self.publish_result.get("success"))
        return {"topic": self.request.topic, "platform": self.request.platform,
                "content_length": len(self.text), "quality_score": self.quality_score,
                "image_prompt": self.image_prompt[:200], "image_url": self.image_url,
                "publish_ready": bool(self.publish_package), "published": published,
                "publish_result": self.publish_result, "analytics": self.analytics,
                "steps_completed": sum(s.status == "success" for s in self.steps),
                "steps_failed": sum(s.status == "error" for s in self.steps),
                "steps_skipped": sum(s.status == "skipped" for s in self.steps),
                "total_duration_ms": round(self.total_duration_ms, 1),
                "steps": [s.to_dict() for s in self.steps]}


class PipelineLogger:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def log(self, layer: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.events.append({"time": time.time(), "layer": layer, "event": event, "data": data or {}})
        print(f"[{layer}] {event}")


class PipelineWiring:
    """Canonical single-run execution graph for UCOS."""

    def __init__(self) -> None:
        self._logger = PipelineLogger()
        self._key_manager = None
        self._gemini = None
        self._init_ai()

    def _init_ai(self) -> None:
        try:
            from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
            from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
            self._key_manager = KeyManager()
            for idx, (env_name, secret_name) in enumerate(_GEMINI_KEYS, 1):
                key = os.environ.get(env_name) or os.environ.get(secret_name)
                if key:
                    self._key_manager.register_key(f"k{idx}", key, "gemini")
            self._gemini = GeminiProvider(self._key_manager)
        except Exception as exc:
            self._logger.log("L12-AI", f"init unavailable: {exc}")

    def _run_step(self, response: ContentResponse, layer: str, fn, required: bool = True) -> bool:
        step = PipelineStepResult(layer)
        response.steps.append(step)
        started = time.time()
        try:
            data = fn() or {}
            step.data = data
            step.status = "skipped" if data.get("skipped") else "success"
            return True
        except Exception as exc:
            step.status = "error"
            step.error = str(exc)
            self._logger.log(layer, f"{'failed' if required else 'warning'}: {exc}")
            return False
        finally:
            step.duration_ms = (time.time() - started) * 1000

    def _research(self, req: ContentRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer02_research.modules.topic_intelligence.topic_intel_manager import TopicIntelManager
        entry = TopicIntelManager().add_topic(name=req.topic, niche=req.platform, category=req.style, confidence=0.5)
        ctx["topic_id"] = getattr(entry, "topic_id", "")
        return {"topic_id": ctx["topic_id"]}

    def _intelligence(self, req: ContentRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
        result = ContentAnalyzer().analyze(req.topic, domain=req.platform)
        ctx["keywords"] = getattr(result, "keywords", [])
        ctx["entities"] = getattr(result, "entities", [])
        ctx["intent"] = getattr(result, "intent", "informational")
        return {"keywords": ctx["keywords"], "intent": ctx["intent"]}

    def _writing(self, req: ContentRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager
        result = PlannerManager().create_plan(topic=req.topic, platform=req.platform, user_goal="educate",
                                              audience_hint="general", tone_override=req.tone)
        plan = getattr(result, "plan", None)
        ctx["writing_plan"] = plan
        return {"plan_id": getattr(plan, "plan_id", ""), "structure": getattr(plan, "structure", {})}

    def _ai(self, req: ContentRequest, ctx: Dict[str, Any], response: ContentResponse) -> Dict[str, Any]:
        keywords = ", ".join(map(str, ctx.get("keywords", [])[:8]))
        configured = bool(self._gemini and self._key_manager and self._key_manager.get_stats().get("total_keys", 0))
        if not configured:
            response.text = (f"{req.topic}\n\nKey points to investigate and explain: {keywords or req.topic}.\n\n"
                             "Offline draft only; connect a configured AI provider before production publishing.")[:req.max_length]
            ctx["ai_model"] = "offline-draft"
            return {"model": "offline-draft", "content_length": len(response.text), "offline": True}
        prompt = (f"Create a high-quality {req.platform} {req.style} post about: {req.topic}\n\n"
                  f"Tone: {req.tone}\nKeywords: {keywords}\nMaximum length: {req.max_length} characters.\n"
                  "Use accurate information; do not invent statistics or sources. Return only the final post.")
        result = self._gemini.generate(prompt, system_prompt=f"You are an expert {req.platform} content writer.")
        content = (result.get("content") or "").strip()
        if not content:
            raise RuntimeError("L12 returned empty content")
        response.text = content[:req.max_length].rstrip()
        ctx["ai_model"] = result.get("model", "gemini")
        return {"model": ctx["ai_model"], "content_length": len(response.text)}

    def _image(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        if not req.include_image:
            return {"generated": False, "skipped": True, "reason": "disabled"}
        from layers.layer05_image.modules.image_planner.image_planner import ImagePlanner
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        plans = ImagePlanner().plan(req.topic, platform=req.platform, image_type="photo", count=1)
        image_type = getattr(plans[0], "image_type", "photo") if plans else "photo"
        prompt = f"Create a {image_type} image for a {req.platform} post about '{req.topic}'. Professional, factual, engaging, no misleading text."
        response.image_prompt = prompt
        result = GeminiImageProvider().generate(prompt, size="1024x1024", style=req.tone)
        response.image_url = getattr(result, "image_url", "") or ""
        ctx["image_generated"] = bool(response.image_url or getattr(result, "image_data", None))
        return {"generated": ctx["image_generated"], "provider": getattr(result, "provider", ""), "image_url": response.image_url}

    def _quality(self, req: ContentRequest, response: ContentResponse) -> Dict[str, Any]:
        from layers.layer06_quality.modules.content_quality_analyzer.quality_analyzer import ContentQualityAnalyzer
        report = ContentQualityAnalyzer().analyze(response.text, platform=req.platform)
        response.quality_score = float(getattr(report, "overall_score", 0.0))
        response.quality_report = report.to_dict() if hasattr(report, "to_dict") else {}
        if response.quality_score < 5.0:
            raise RuntimeError(f"Quality gate rejected content: score={response.quality_score}")
        return {"quality_score": response.quality_score}

    def _publisher(self, req: ContentRequest):
        from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
        manager = PublisherManager()
        publisher = manager.plugin_manager.registry.get_instance(req.platform)
        if publisher is None:
            return None, manager
        credentials = {}
        if req.platform == "facebook":
            credentials = {"page_id": os.environ.get("FACEBOOK_PAGE_ID", ""),
                           "access_token": os.environ.get("FACEBOOK_ACCESS_TOKEN", "")}
        if not all(credentials.values()) or not publisher.authenticate(credentials):
            return None, manager
        return manager, publisher

    def _publish(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
        from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
        manager, _ = self._publisher(req)
        if manager is None:
            response.publish_result = {"success": False, "platform": req.platform, "post_id": None,
                                       "url": None, "error": "No real publisher credentials/adapter configured"}
            return {"published": False, "skipped": True, "reason": "publisher_unconfigured"}
        request = PublishRequest(platform=req.platform, content=response.text,
                                 content_type="photo" if response.image_url else "post")
        digest = hashlib.sha256(response.text.encode("utf-8")).hexdigest()[:24]
        request.idempotency_key = f"ucos:{req.platform}:{digest}"
        request.metadata.update({"topic": req.topic, "ai_model": ctx.get("ai_model", "unknown")})
        for key in ("account_id", "template_id"):
            if req.metadata.get(key):
                request.metadata[key] = req.metadata[key]
        if response.image_url:
            asset = MediaAsset(file_path=response.image_url, media_type="image")
            asset.file_name = response.image_url.rsplit("/", 1)[-1] or "generated-image"
            asset.platform_ready = True
            request.media_assets.append(asset)
        result = manager.publish(request)
        data = {"success": bool(result.success), "platform": req.platform, "post_id": result.post_id,
                "url": result.url, "error": result.error_message, "duration_ms": result.duration_ms}
        response.publish_result = data
        if not result.success:
            raise RuntimeError(result.error_message or "Publisher returned failure")
        response.publish_package = request.to_dict()
        ctx["post_id"] = result.post_id
        return data

    def _analytics(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        post_id = ctx.get("post_id")
        if not post_id:
            return {"published": False, "skipped": True, "reason": "no_real_post_id"}
        manager, publisher = self._publisher(req)
        if manager is None or publisher is None:
            return {"published": False, "skipped": True, "reason": "publisher_unconfigured"}
        metrics = publisher.get_analytics(post_id)
        response.analytics = {"platform": req.platform, "post_id": post_id, "metrics": metrics, "collected_at": time.time()}
        return response.analytics

    def _learning(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer09_learning.modules.learning_engine.learning_memory import LearningMemory
        from layers.layer09_learning.modules.learning_engine.lesson_generator import Lesson
        lesson = Lesson(lesson_type="content_execution", title=f"Executed '{req.topic}' for {req.platform}")
        lesson.description = (f"quality={response.quality_score}; published="
                              f"{bool(response.publish_result and response.publish_result.get('success'))}; "
                              f"analytics={response.analytics if response.analytics is not None else 'UNKNOWN'}")
        lesson.confidence = max(0.0, min(1.0, response.quality_score / 10.0))
        lesson.platform = req.platform
        lesson.category = req.tone
        entry = LearningMemory().store_lesson(lesson)
        data = entry.to_dict() if hasattr(entry, "to_dict") else {"id": "stored"}
        response.learning_entries.append(data)
        return {"stored": True, "entry": data}

    def execute(self, request: ContentRequest) -> ContentResponse:
        if not request.topic:
            raise ValueError("topic is required")
        response = ContentResponse(request)
        ctx: Dict[str, Any] = {}
        started = time.time()
        steps = (("L2-Research", lambda: self._research(request, ctx)),
                 ("L3-Intelligence", lambda: self._intelligence(request, ctx)),
                 ("L4-Writing", lambda: self._writing(request, ctx)),
                 ("L12-AI", lambda: self._ai(request, ctx, response)),
                 ("L5-Image", lambda: self._image(request, response, ctx)),
                 ("L6-Quality", lambda: self._quality(request, response)),
                 ("L7-Publish", lambda: self._publish(request, response, ctx)))
        for layer, fn in steps:
            if not self._run_step(response, layer, fn):
                break
        if not any(s.layer == "L8-Analytics" for s in response.steps):
            self._run_step(response, "L8-Analytics", lambda: self._analytics(request, response, ctx), required=False)
        if not any(s.layer == "L9-Learning" for s in response.steps):
            self._run_step(response, "L9-Learning", lambda: self._learning(request, response, ctx), required=False)
        response.total_duration_ms = (time.time() - started) * 1000
        response.stats = {"execution_time_ms": round(response.total_duration_ms, 1),
                          "published": bool(response.publish_result and response.publish_result.get("success")),
                          "post_id": ctx.get("post_id", "")}
        self._persist(response)
        return response

    def _persist(self, response: ContentResponse) -> None:
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
            persist = PipelinePersistence()
            try:
                persist.save_pipeline_run(response.to_dict())
            finally:
                persist.close()
        except Exception as exc:
            self._logger.log("L13/L14-Persistence", f"warning: {exc}")

    def status(self) -> Dict[str, Any]:
        stats = self._key_manager.get_stats() if self._key_manager else {}
        return {"pipeline": "canonical", "ai_engine": "gemini" if self._gemini else "unavailable",
                "api_keys_configured": stats.get("total_keys", 0), "healthy_keys": stats.get("healthy", 0)}
