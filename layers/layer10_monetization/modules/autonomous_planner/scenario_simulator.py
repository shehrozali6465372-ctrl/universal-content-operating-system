"""ScenarioSimulator — Simulate multiple execution paths."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_SS_COUNTER = itertools.count(1)


class Scenario:
    """An execution scenario to simulate."""

    __slots__ = ("scenario_id", "name", "steps", "predicted_outcome",
                 "confidence", "risk_level", "simulated_at")

    def __init__(self, name: str = "") -> None:
        self.scenario_id: str = f"scen_{next(_SS_COUNTER)}"
        self.name = name
        self.steps: List[Dict[str, str]] = []
        self.predicted_outcome: Dict[str, Any] = {}
        self.confidence: float = 0.5
        self.risk_level: str = "medium"
        self.simulated_at: float = 0.0

    def add_step(self, layer: str, action: str, expected_result: str = "") -> None:
        self.steps.append({"layer": layer, "action": action, "expected": expected_result})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id, "name": self.name,
            "steps": len(self.steps), "confidence": round(self.confidence, 3),
            "risk_level": self.risk_level,
        }


class ScenarioSimulator:
    """Simulate and compare multiple execution paths."""

    def __init__(self) -> None:
        self._scenarios: List[Scenario] = []
        self._simulation_results: List[Dict[str, Any]] = []

    def create_scenario(self, name: str, steps: Optional[List[Dict[str, str]]] = None) -> Scenario:
        scenario = Scenario(name)
        if steps:
            for step in steps:
                scenario.add_step(step.get("layer", ""), step.get("action", ""),
                                  step.get("expected", ""))
        self._scenarios.append(scenario)
        return scenario

    def simulate(self, scenario_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[Scenario]:
        for scenario in self._scenarios:
            if scenario.scenario_id == scenario_id:
                scenario.simulated_at = time.time()
                step_count = len(scenario.steps)
                scenario.confidence = min(0.95, 0.3 + step_count * 0.1)
                scenario.risk_level = "low" if step_count <= 3 else "medium" if step_count <= 6 else "high"
                scenario.predicted_outcome = {
                    "success_probability": scenario.confidence,
                    "estimated_duration_ms": step_count * 500,
                    "resource_cost": step_count * 0.1,
                }
                self._simulation_results.append({
                    "scenario_id": scenario_id, "outcome": scenario.predicted_outcome,
                })
                return scenario
        return None

    def compare_scenarios(self) -> List[Scenario]:
        return sorted(self._scenarios, key=lambda s: s.confidence, reverse=True)

    def choose_best(self) -> Optional[Scenario]:
        if not self._scenarios:
            return None
        return max(self._scenarios, key=lambda s: s.confidence)

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        for s in self._scenarios:
            if s.scenario_id == scenario_id:
                return s
        return None

    def get_stats(self) -> Dict[str, Any]:
        return {"total_scenarios": len(self._scenarios),
                "simulations_run": len(self._simulation_results)}
