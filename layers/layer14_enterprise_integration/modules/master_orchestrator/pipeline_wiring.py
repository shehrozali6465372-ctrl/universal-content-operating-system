"""Canonical UCOS content pipeline.

Research -> intelligence -> writing -> AI -> image -> quality -> publishing
-> analytics -> learning -> persistence. External publishing and analytics are
reported only when a real adapter and real credentials are available.
"""
from __future__ import annotations

import hashlib
import os
import time
import uuid
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
                "content": self.text, "content_length": len(self.text), "quality_score": self.quality_score,
                "image_prompt": self.image_prompt[:200], "image_url": self.image_url,
                "publish_ready": bool(self.publish_package), "published": published,
                "publish_result": self.publish_result, "post_id": (self.publish_result or {}).get("post_id"),
                "analytics": self.analytics,
                "steps_completed": sum(s.status == "success" for s in self.steps),
                "steps_failed": sum(s.status == "error" for s in self.steps),
                "steps_skipped": sum(s.status == "skipped" for s in self.steps),
                "total_duration_ms": round(self.total_duration_ms, 1),
                "steps": [s.to_dict() for s in self.steps],
                "metadata": dict(self.request.metadata)}


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
        self._router = None
        self._init_ai()

    def _init_ai(self) -> None:
        try:
            from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
            from layers.layer12_ai_foundation.modules.model_router.model_router import ModelResponse, ModelRouter, RequestType
            from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
            self._key_manager = KeyManager()
            for idx, (env_name, secret_name) in enumerate(_GEMINI_KEYS, 1):
                key = os.environ.get(env_name) or os.environ.get(secret_name)
                if key:
                    self._key_manager.register_key(f"k{idx}", key, "gemini")
            self._gemini = GeminiProvider(self._key_manager)
            self._router = ModelRouter(self._key_manager)

            def gemini_handler(request):
                result = self._gemini.generate(
                    request.prompt,
                    model=request.model,
                    system_prompt=request.system_prompt,
                    **request.parameters,
                )
                content = (result.get("content") or "").strip()
                if not content:
                    raise RuntimeError(result.get("error") or "Gemini returned empty content")
                response = ModelResponse(request.request_id, content)
                response.provider = result.get("provider", "gemini")
                response.model_used = result.get("model", request.model or "gemini")
                response.tokens_used = int(result.get("tokens_used") or 0)
                response.metadata = {"raw_provider": result.get("provider", "gemini")}
                return response

            self._router.register_provider("gemini", handler=gemini_handler,
                                           capabilities=[RequestType.TEXT, RequestType.CHAT])
            self._router.set_routing(RequestType.TEXT, ["gemini"])
            self._router.set_routing(RequestType.CHAT, ["gemini"])
        except Exception as exc:
            self._logger.log("L12-AI", f"init unavailable: {exc}")
            self._router = None

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

        production = os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}
        external_research = production or os.environ.get("UCOS_ENABLE_EXTERNAL_RESEARCH", "").lower() == "true"
        niche = str(req.metadata.get("niche") or "general").strip().lower()

        if external_research:
            from layers.layer14_enterprise_integration.modules.real_integrations import IntegrationGateway
            result = IntegrationGateway().search(req.topic, location=req.metadata.get("location"))
            results = result.get("results") or []
            if not results:
                raise RuntimeError("real research provider returned no usable source results")
            source = results[0]
            source_id = str(source["source_id"])
            keywords = [str(item.get("title") or "").strip() for item in results[:8] if str(item.get("title") or "").strip()]
            entry = TopicIntelManager().add_topic(
                name=req.topic, niche=niche, category=req.style,
                keywords=keywords, source_trend_id=source_id, confidence=1.0,
            )
            ctx["topic_id"] = getattr(entry, "topic_id", "")
            ctx["research_provider"] = result.get("provider", "serpapi")
            ctx["research_source_id"] = source_id
            ctx["research_results"] = results
            return {"topic_id": ctx["topic_id"], "provider": ctx["research_provider"],
                    "source_id": source_id, "result_count": len(results)}

        entry = TopicIntelManager().add_topic(name=req.topic, niche=niche, category=req.style, confidence=0.0)
        ctx["topic_id"] = getattr(entry, "topic_id", "")
        ctx["research_observed"] = False
        return {"topic_id": ctx["topic_id"], "observed": False}

    def _intelligence(self, req: ContentRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
        domain = str(req.metadata.get("niche") or "general").strip().lower()
        result = ContentAnalyzer().analyze(req.topic, domain=domain)
        ctx["keywords"] = list(getattr(getattr(result, "keyword_analysis", None), "keywords", []) or [])
        ctx["entities"] = list(getattr(result, "entities", []) or [])
        ctx["intent"] = getattr(getattr(result, "intent", None), "primary_intent", "informational")
        ctx["intelligence"] = result.to_dict() if hasattr(result, "to_dict") else {}
        return {"keywords": ctx["keywords"], "entities": ctx["entities"], "intent": ctx["intent"], "intelligence": ctx["intelligence"]}

    def _writing(self, req: ContentRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager
        intelligence_data = {
            "intent": ctx.get("intent"),
            "keywords": list(ctx.get("keywords", []) or []),
            "entities": list(ctx.get("entities", []) or []),
            "intelligence": ctx.get("intelligence", {}),
        }
        result = PlannerManager().create_plan(
            topic=req.topic, platform=req.platform, user_goal="educate",
            audience_hint="general", tone_override=req.tone,
            intelligence_data=intelligence_data,
        )
        plan = getattr(result, "plan", None)
        ctx["writing_plan"] = plan
        return {"plan_id": getattr(plan, "plan_id", ""), "structure": getattr(plan, "structure", {})}

    def _ai(self, req: ContentRequest, ctx: Dict[str, Any], response: ContentResponse) -> Dict[str, Any]:
        keywords = ", ".join(map(str, ctx.get("keywords", [])[:8]))
        configured = bool(self._router and self._gemini and self._key_manager and
                          self._key_manager.get_stats().get("total_keys", 0))
        if not configured:
            response.text = (f"{req.topic}\n\nKey points to investigate and explain: {keywords or req.topic}.\n\n"
                             "Offline draft only; connect a configured AI provider before production publishing.")[:req.max_length]
            ctx["ai_model"] = "offline-draft"
            return {"model": "offline-draft", "content_length": len(response.text), "offline": True}
        prompt = (f"Create a high-quality {req.platform} {req.style} post about: {req.topic}\n\n"
                  f"Tone: {req.tone}\nKeywords: {keywords}\nMaximum length: {req.max_length} characters.\n"
                  "Use accurate information; do not invent statistics or sources. Return only the final post.")
        routed = self._router.generate_text(
            prompt,
            system_prompt=f"You are an expert {req.platform} content writer.",
        )
        content = (routed.content or "").strip()
        if not content:
            detail = routed.metadata.get("error", "No provider returned content")
            raise RuntimeError(f"L12 AI routing failed: {detail}")
        response.text = content[:req.max_length].rstrip()
        ctx["ai_model"] = routed.model_used or "gemini"
        ctx["ai_provider"] = routed.provider or "gemini"
        return {"model": ctx["ai_model"], "provider": ctx["ai_provider"],
                "content_length": len(response.text), "router_request_id": routed.request_id}

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
        if response.quality_score < 0.7:
            raise RuntimeError(f"Quality gate rejected content: score={response.quality_score}")
        return {"quality_score": response.quality_score}

    def _publisher(self, req: ContentRequest):
        from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
        if not req.metadata.get("account_id"):
            raise ValueError("account_id is required for production publishing")
        from layers.layer07_publishing.modules.account_control.meta_credentials import MetaCredentialProvider
        manager = PublisherManager()
        publisher = manager.plugin_manager.registry.get_instance(req.platform)
        if publisher is None:
            return None, manager
        credentials = MetaCredentialProvider().credentials_for(req.platform, str(req.metadata["account_id"]))
        if not publisher.authenticate(credentials):
            raise RuntimeError(f"real {req.platform} credentials rejected")
        return manager, publisher

    def _publish(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
        from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
        if str(ctx.get("ai_model", "")).lower() == "offline-draft":
            response.publish_result = {"success": False, "platform": req.platform, "post_id": None,
                                       "url": None, "error": "Offline draft cannot enter production publishing"}
            raise RuntimeError("Production publishing blocked: AI provider is offline-draft")
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
        production = os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}
        observed_outcome = bool(response.analytics is not None and response.analytics.get("metrics") is not None)
        if production and not observed_outcome:
            return {"stored": False, "skipped": True, "reason": "no_observed_external_outcome"}

        from layers.layer09_learning.modules.learning_engine.learning_memory import LearningMemory
        from layers.layer09_learning.modules.learning_engine.lesson_generator import Lesson
        lesson = Lesson(lesson_type="content_execution", title=f"Executed '{req.topic}' for {req.platform}")
        lesson.description = (f"quality={response.quality_score}; published="
                              f"{bool(response.publish_result and response.publish_result.get('success'))}; "
                              f"analytics={response.analytics if response.analytics is not None else 'UNKNOWN'}")
        lesson.confidence = max(0.0, min(1.0, response.quality_score))
        lesson.platform = req.platform
        lesson.category = req.tone
        entry = LearningMemory().store_lesson(lesson)
        data = entry.to_dict() if hasattr(entry, "to_dict") else {"id": "stored"}
        response.learning_entries.append(data)
        return {"stored": True, "entry": data}

    def execute(self, request: ContentRequest) -> ContentResponse:
        if not request.topic:
            raise ValueError("topic is required")
        request.metadata.setdefault("lineage_id", str(uuid.uuid4()))
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
        request.metadata["topic_id"] = ctx.get("topic_id", "")
        request.metadata["research_provider"] = ctx.get("research_provider", "")
        request.metadata["research_source_id"] = ctx.get("research_source_id", "")
        request.metadata["ai_provider"] = ctx.get("ai_provider", "")
        request.metadata["post_id"] = ctx.get("post_id", "")
        request.metadata["niche"] = request.metadata.get("niche") or "general"
        response.stats = {"execution_time_ms": round(response.total_duration_ms, 1),
                          "published": bool(response.publish_result and response.publish_result.get("success")),
                          "post_id": ctx.get("post_id", "")}
        self._persist(response)
        return response

    def _persist(self, response: ContentResponse) -> None:
        production = os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}
        if not production:
            try:
                from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
                persist = PipelinePersistence()
                try:
                    persist.save_pipeline_run(response.to_dict())
                finally:
                    persist.close()
            except Exception as exc:
                self._logger.log("L13/L14-Persistence", f"warning: {exc}")
        enabled = os.environ.get("UCOS_ENABLE_LINEAGE", "true" if production else "false").lower() == "true"
        if not enabled:
            return
        try:
            from layers.layer14_enterprise_integration.modules.real_integrations import LineageStore
            metadata = response.request.metadata
            store = LineageStore()
            try:
                parent = None

                research_source_id = str(metadata.get("research_source_id") or "")
                research_provider = str(metadata.get("research_provider") or "")
                if research_source_id and research_provider:
                    event = store.record(
                        lineage_id=str(metadata["lineage_id"]), stage="source",
                        entity_id=research_source_id, source=research_provider,
                        source_id=research_source_id, provider=research_provider,
                        status="observed", payload={"query": response.request.topic},
                    )
                    parent = event.event_id

                    event = store.record(
                        lineage_id=str(metadata["lineage_id"]), stage="niche",
                        entity_id=str(metadata.get("niche") or "general"),
                        source=research_provider, source_id=research_source_id,
                        provider=research_provider, status="observed",
                        payload={"niche": metadata.get("niche")},
                        parent_event_id=parent,
                    )
                    parent = event.event_id

                    event = store.record(
                        lineage_id=str(metadata["lineage_id"]), stage="keyword",
                        entity_id=hashlib.sha256(response.request.topic.encode("utf-8")).hexdigest(),
                        source=research_provider, source_id=research_source_id,
                        provider=research_provider, status="observed",
                        payload={"seed_keyword": response.request.topic},
                        parent_event_id=parent,
                    )
                    parent = event.event_id

                    event = store.record(
                        lineage_id=str(metadata["lineage_id"]), stage="content",
                        entity_id=hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
                        source="ucos", source_id=str(metadata.get("topic_id") or response.request.topic),
                        provider=str(metadata.get("ai_provider") or metadata.get("ai_model") or "unknown"),
                        status="observed", payload={"content_length": len(response.text)},
                        parent_event_id=parent,
                    )
                    parent = event.event_id

                    asset_value = response.image_url or hashlib.sha256(response.text.encode("utf-8")).hexdigest()
                    asset_payload = (
                        {"url": response.image_url, "asset_type": "image"}
                        if response.image_url
                        else {"asset_type": "text", "content_hash": asset_value}
                    )
                    event = store.record(
                        lineage_id=str(metadata["lineage_id"]), stage="asset",
                        entity_id=hashlib.sha256(str(asset_value).encode("utf-8")).hexdigest(),
                        source="ucos", source_id=str(asset_value),
                        provider="runtime-media" if response.image_url else str(metadata.get("ai_provider") or "unknown"),
                        status="observed", payload=asset_payload,
                        parent_event_id=parent,
                    )
                    parent = event.event_id

                    event = store.record(
                        lineage_id=str(metadata["lineage_id"]), stage="platform",
                        entity_id=response.request.platform,
                        source="ucos", source_id=response.request.platform,
                        provider="ucos", status="observed",
                        payload={"platform": response.request.platform},
                        parent_event_id=parent,
                    )
                    parent = event.event_id

                    account_id = str(metadata.get("account_id") or "")
                    if account_id:
                        event = store.record(
                            lineage_id=str(metadata["lineage_id"]), stage="account",
                            entity_id=account_id, source="ucos",
                            source_id=account_id, provider="ucos",
                            status="observed", payload={"account_id": account_id},
                            parent_event_id=parent,
                        )
                        parent = event.event_id

                    post_id = str(metadata.get("post_id") or "")
                    if post_id:
                        event = store.record(
                            lineage_id=str(metadata["lineage_id"]), stage="publish",
                            entity_id=post_id, source=response.request.platform,
                            source_id=post_id, provider=response.request.platform,
                            status="observed",
                            payload={"url": (response.publish_result or {}).get("url")},
                            parent_event_id=parent,
                        )
                        parent = event.event_id

                    metrics = (response.analytics or {}).get("metrics") if isinstance(response.analytics, dict) else None
                    if isinstance(metrics, dict):
                        click_value = metrics.get("clicks", metrics.get("click_count"))
                        conversion_value = metrics.get("conversions", metrics.get("conversion_count"))
                        revenue_value = metrics.get("revenue", metrics.get("revenue_amount"))
                        if click_value is not None:
                            event = store.record(
                                lineage_id=str(metadata["lineage_id"]), stage="click",
                                entity_id=f"{post_id}:clicks", source=response.request.platform,
                                source_id=post_id, provider=response.request.platform,
                                status="observed", payload={"clicks": click_value},
                                parent_event_id=parent,
                            )
                            parent = event.event_id
                        if conversion_value is not None and click_value is not None:
                            event = store.record(
                                lineage_id=str(metadata["lineage_id"]), stage="conversion",
                                entity_id=f"{post_id}:conversions", source=response.request.platform,
                                source_id=post_id, provider=response.request.platform,
                                status="observed", payload={"conversions": conversion_value},
                                parent_event_id=parent,
                            )
                            parent = event.event_id
                        if revenue_value is not None and conversion_value is not None and click_value is not None:
                            store.record(
                                lineage_id=str(metadata["lineage_id"]), stage="revenue",
                                entity_id=f"{post_id}:revenue", source=response.request.platform,
                                source_id=post_id, provider=response.request.platform,
                                status="observed", payload={"revenue": revenue_value},
                                parent_event_id=parent,
                            )
            finally:
                store.close()
        except Exception as exc:
            self._logger.log("L13/L14-Lineage", f"{'error' if production else 'warning'}: {exc}")
            if production:
                raise

    def status(self) -> Dict[str, Any]:
        stats = self._key_manager.get_stats() if self._key_manager else {}
        return {"pipeline": "canonical", "ai_engine": "model-router/gemini" if self._router else "unavailable",
                "ai_router_providers": self._router.list_providers() if self._router else [],
                "api_keys_configured": stats.get("total_keys", 0), "healthy_keys": stats.get("healthy", 0)}
