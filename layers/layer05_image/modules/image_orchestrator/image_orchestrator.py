"""Image Orchestrator — Coordinates all image modules."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer05_image.modules.image_planner.image_planner import ImagePlanner, ImagePlan
from layers.layer05_image.modules.image_prompt.image_prompt import ImagePromptBuilder, ImagePrompt
from layers.layer05_image.modules.image_provider.image_provider import BaseImageProvider, MockImageProvider
from layers.layer05_image.modules.layout_engine.layout_engine import LayoutEngine
from layers.layer05_image.modules.thumbnail_engine.thumbnail_engine import ThumbnailEngine
from layers.layer05_image.modules.carousel_planner.carousel_planner import CarouselPlanner
from layers.layer05_image.modules.infographic_engine.infographic_engine import InfographicEngine
from layers.layer05_image.modules.image_optimizer.image_optimizer import ImageOptimizer
from layers.layer05_image.modules.image_memory.image_memory import ImageMemory


class ImageOrchestratorResult:
    """Result from the Image Orchestrator."""
    __slots__ = ("topic", "platform", "image_plan", "prompt", "layout",
                 "image_response", "optimization", "metadata", "pipeline_time_ms")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.platform = ""
        self.image_plan: Optional[ImagePlan] = None
        self.prompt: Optional[ImagePrompt] = None
        self.layout = None
        self.image_response = None
        self.optimization = None
        self.metadata: Dict[str, Any] = {}
        self.pipeline_time_ms = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "platform": self.platform,
            "image_plan": self.image_plan.to_dict() if self.image_plan else None,
            "prompt": self.prompt.to_dict() if self.prompt else None,
            "layout": self.layout.to_dict() if self.layout else None,
            "image": self.image_response.to_dict() if self.image_response else None,
            "optimization": self.optimization.to_dict() if self.optimization else None,
            "pipeline_time_ms": round(self.pipeline_time_ms, 2),
        }


class ImageOrchestrator:
    """Coordinates all image modules.

    Pipeline: Plan → Prompt → Layout → Generate → Optimize → Store
    """

    def __init__(self, provider: Optional[BaseImageProvider] = None) -> None:
        self.planner = ImagePlanner()
        self.prompt_builder = ImagePromptBuilder()
        self.provider = provider or MockImageProvider()
        self.layout_engine = LayoutEngine()
        self.thumbnail = ThumbnailEngine()
        self.carousel = CarouselPlanner()
        self.infographic = InfographicEngine()
        self.optimizer = ImageOptimizer()
        self.memory = ImageMemory()
        self._run_count = 0

    def run(self, topic: str, platform: str = "facebook",
            image_type: str = "photo", style: str = "modern") -> ImageOrchestratorResult:
        """Full pipeline: topic → planned image."""
        start = time.time()
        result = ImageOrchestratorResult(topic=topic)
        result.platform = platform

        # Plan
        plans = self.planner.plan(topic, platform, image_type)
        result.image_plan = plans[0] if plans else None

        # Prompt
        result.prompt = self.prompt_builder.build(
            f"{image_type} about {topic}", style=style, platform=platform
        )

        # Layout
        result.layout = self.layout_engine.get_layout(platform, image_type)

        # Generate (mock)
        if self.provider.is_configured():
            result.image_response = self.provider.generate(result.prompt.text)

        # Optimize
        dims = result.layout
        result.optimization = self.optimizer.optimize(
            dims.width, dims.height, platform
        )

        # Store
        self.memory.store_image(
            platform=platform, topic=topic,
            url=result.image_response.image_url if result.image_response else "",
        )

        result.pipeline_time_ms = (time.time() - start) * 1000
        self._run_count += 1
        return result

    def run_multi_platform(self, topic: str, platforms: Optional[List[str]] = None) -> List[ImageOrchestratorResult]:
        plats = platforms or ["facebook", "instagram", "twitter", "linkedin"]
        return [self.run(topic, p) for p in plats]

    @property
    def run_count(self) -> int:
        return self._run_count
