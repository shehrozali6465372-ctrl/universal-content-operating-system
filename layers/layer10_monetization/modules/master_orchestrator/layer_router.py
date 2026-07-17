"""Layer Router — Route work to the correct layer."""
from __future__ import annotations
from typing import Callable, Dict, List, Optional


class LayerRoute:
    """A registered route to a layer."""

    __slots__ = ("layer_id", "layer_name", "handler", "priority", "required")

    def __init__(self, layer_id: str = "", layer_name: str = "") -> None:
        self.layer_id = layer_id
        self.layer_name = layer_name
        self.handler: Optional[Callable] = None
        self.priority: int = 0
        self.required: bool = True


class LayerRouter:
    """Route requests to appropriate layers based on task type."""

    DEFAULT_ROUTES: Dict[str, str] = {
        "research": "layer02_research",
        "research_query": "layer02_research",
        "fact_check": "layer02_research",
        "trend_analysis": "layer03_intelligence",
        "content_understanding": "layer03_intelligence",
        "reasoning": "layer03_intelligence",
        "write": "layer04_writing",
        "draft": "layer04_writing",
        "caption": "layer04_writing",
        "generate_image": "layer05_image",
        "image_plan": "layer05_image",
        "quality_check": "layer06_quality",
        "safety_check": "layer06_quality",
        "seo_check": "layer06_quality",
        "publish": "layer07_publishing",
        "schedule": "layer07_publishing",
        "analytics": "layer08_analytics",
        "learn": "layer09_learning",
        "optimize": "layer09_learning",
        "predict": "layer09_learning",
    }

    def __init__(self) -> None:
        self._routes: Dict[str, LayerRoute] = {}
        for task, layer in self.DEFAULT_ROUTES.items():
            route = LayerRoute(layer, layer)
            self._routes[task] = route

    def route(self, task_type: str) -> Optional[LayerRoute]:
        return self._routes.get(task_type)

    def register(self, task_type: str, layer_id: str,
                 handler: Optional[Callable] = None, priority: int = 0,
                 required: bool = True) -> LayerRoute:
        route = LayerRoute(layer_id, layer_id)
        route.handler = handler
        route.priority = priority
        route.required = required
        self._routes[task_type] = route
        return route

    def unregister(self, task_type: str) -> bool:
        if task_type in self._routes:
            del self._routes[task_type]
            return True
        return False

    def get_layer_for_task(self, task_type: str) -> str:
        route = self.route(task_type)
        return route.layer_id if route else ""

    def get_tasks_for_layer(self, layer_id: str) -> List[str]:
        return [t for t, r in self._routes.items() if r.layer_id == layer_id]

    def get_all_routes(self) -> Dict[str, str]:
        return {t: r.layer_id for t, r in self._routes.items()}

    @property
    def route_count(self) -> int:
        return len(self._routes)
