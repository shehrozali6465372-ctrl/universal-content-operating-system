"""ReasoningOrchestrator — full reasoning pipeline orchestrator."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .logical_reasoner import LogicalReasoner
from .analytical_reasoner import AnalyticalReasoner
from .creative_reasoner import CreativeReasoner
from .strategic_reasoner import StrategicReasoner
from .planning_reasoner import PlanningReasoner
from .reflection_reasoner import ReflectionReasoner
from .decision_reasoner import DecisionReasoner
from .verification_reasoner import VerificationReasoner
from .reasoning_config import ReasoningConfig
from .reasoning_metrics import ReasoningMetrics
from .reasoning_events import ReasoningEvents
from .reasoning_health import ReasoningHealth
from .reasoning_cache import ReasoningCache
from .reasoning_router import ReasoningRouter
from .models import ReasoningResult, ReasoningType


class ReasoningOrchestrator:
    """Full reasoning pipeline orchestrator."""

    def __init__(self, config: Optional[ReasoningConfig] = None) -> None:
        self.config = config or ReasoningConfig()
        self.logical = LogicalReasoner()
        self.analytical = AnalyticalReasoner()
        self.creative = CreativeReasoner()
        self.strategic = StrategicReasoner()
        self.planning = PlanningReasoner()
        self.reflection = ReflectionReasoner()
        self.decision = DecisionReasoner()
        self.verification = VerificationReasoner()
        self.metrics = ReasoningMetrics()
        self.events = ReasoningEvents()
        self.health = ReasoningHealth()
        self.cache = ReasoningCache()
        self.router = ReasoningRouter()
        self._is_running = False

    def start(self) -> bool:
        self._is_running = True
        self.events.publish("reasoning_started")
        return True

    def stop(self) -> bool:
        self._is_running = False
        self.events.publish("reasoning_stopped")
        return True

    def reason(self, problem: str, reasoning_type: str = "logical",
               context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        start = time.time()

        # Route to appropriate reasoner
        rt = self.router.route(reasoning_type)

        if rt == ReasoningType.LOGICAL:
            result = self.logical.deductive([problem])
        elif rt == ReasoningType.ANALYTICAL:
            result = self.analytical.analyze([{"problem": problem}])
        elif rt == ReasoningType.CREATIVE:
            result = self.creative.brainstorm(problem)
        elif rt == ReasoningType.STRATEGIC:
            result = self.strategic.plan(problem)
        elif rt == ReasoningType.PLANNING:
            result = self.planning.decompose(problem)
        elif rt == ReasoningType.DECISION:
            result = self.decision.decide([problem])
        else:
            result = self.logical.deductive([problem])

        elapsed = (time.time() - start) * 1000
        self.metrics.record(rt.value, result.confidence, elapsed)
        self.events.publish("reasoning_completed", {"type": rt.value})
        return result

    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()

    def get_stats(self) -> Dict[str, Any]:
        return self.metrics.to_dict()
