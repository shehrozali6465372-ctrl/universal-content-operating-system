"""ContentGenerationManager — Complete content generation pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.content_generation.content_generator import ContentGenerator
from layers.layer10_monetization.modules.content_generation.content_template import TemplateLibrary
from layers.layer10_monetization.modules.content_generation.platform_adapter import PlatformAdapter
from layers.layer10_monetization.modules.content_generation.tone_engine import ToneEngine
from layers.layer10_monetization.modules.content_generation.hook_generator import HookGenerator
from layers.layer10_monetization.modules.content_generation.cta_engine import CTAEngine
from layers.layer10_monetization.modules.content_generation.seo_optimizer import SEOOptimizer
from layers.layer10_monetization.modules.content_generation.content_memory import ContentMemory
from layers.layer10_monetization.modules.content_generation.generation_metrics import GenerationMetrics
from layers.layer10_monetization.modules.content_generation.generation_report import GenerationReport

_CGM_COUNTER = itertools.count(1)


class ContentGenerationManager:
    """Complete content generation pipeline.

    Flow: Topic → Generate → Tone → Hooks → CTA → SEO → Adapt → Memory → Report
    """

    def __init__(self) -> None:
        self.generator = ContentGenerator()
        self.templates = TemplateLibrary()
        self.adapter = PlatformAdapter()
        self.tone_engine = ToneEngine()
        self.hook_generator = HookGenerator()
        self.cta_engine = CTAEngine()
        self.seo_optimizer = SEOOptimizer()
        self.memory = ContentMemory()
        self.metrics = GenerationMetrics()
        self._reports: List[GenerationReport] = []

    def generate(self, topic: str, platform: str = "facebook",
                 content_type: str = "social_post",
                 tone: str = "professional",
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        context = context or {}

        # Step 1: Generate base content
        content = self.generator.generate(topic, platform, content_type, context)

        # Step 2: Apply tone
        self.tone_engine.set_tone(tone)

        # Step 3: Generate hooks
        hooks = self.hook_generator.generate(topic, platform=platform, count=2)

        # Step 4: Generate CTAs
        ctas = self.cta_engine.generate(platform, count=2)

        # Step 5: SEO optimization
        seo = self.seo_optimizer.optimize_title(content.title, topic)

        # Step 6: Adapt to platform
        adapted_text = self.adapter.adapt(content.text, platform)

        # Step 7: Store in memory
        self.memory.store(content_type, platform, topic,
                          quality_score=content.quality_score)

        # Step 8: Record metrics
        self.metrics.record_generation(
            platform, content_type, content.generation_time_ms, content.quality_score,
        )

        result = {
            "content": content.to_dict(),
            "adapted_text": adapted_text[:200] + "..." if len(adapted_text) > 200 else adapted_text,
            "tone": self.tone_engine.get_tone().to_dict(),
            "hooks": [h.to_dict() for h in hooks],
            "ctas": [c.to_dict() for c in ctas],
            "seo": seo,
            "platform_rules": self.adapter.get_rules(platform),
            "duration_ms": round((time.time() - start) * 1000, 1),
        }
        return result

    def generate_batch(self, topics: List[str], platform: str = "facebook",
                       content_type: str = "social_post") -> List[Dict[str, Any]]:
        return [self.generate(t, platform, content_type) for t in topics]

    def generate_multi_platform(self, topic: str,
                                 platforms: Optional[List[str]] = None,
                                 content_type: str = "social_post") -> Dict[str, Dict[str, Any]]:
        platforms = platforms or ["facebook", "instagram", "x", "linkedin"]
        results = {}
        for platform in platforms:
            results[platform] = self.generate(topic, platform, content_type)
        return results

    def generate_report(self) -> GenerationReport:
        report = GenerationReport()
        summary = self.metrics.get_summary()
        report.set_summary(summary)
        if summary["avg_quality"] < 0.5:
            report.add_recommendation("Review content quality settings")
        if summary["throughput_per_sec"] < 1:
            report.add_recommendation("Optimize generation pipeline")
        self._reports.append(report)
        return report

    def get_health(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics.get_summary(),
            "memory": self.memory.get_stats(),
            "templates": self.templates.get_stats(),
            "reports": len(self._reports),
        }
