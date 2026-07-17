"""AutonomousPlanningManager — Complete planning pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.autonomous_planner.autonomous_planner import AutonomousPlanner
from layers.layer10_monetization.modules.autonomous_planner.goal_decomposer import GoalDecomposer
from layers.layer10_monetization.modules.autonomous_planner.decision_matrix import DecisionMatrix
from layers.layer10_monetization.modules.autonomous_planner.scenario_simulator import ScenarioSimulator
from layers.layer10_monetization.modules.autonomous_planner.resource_planner import ResourcePlanner
from layers.layer10_monetization.modules.autonomous_planner.risk_manager import RiskManager
from layers.layer10_monetization.modules.autonomous_planner.adaptive_planner import AdaptivePlanner
from layers.layer10_monetization.modules.autonomous_planner.opportunity_detector import OpportunityDetector
from layers.layer10_monetization.modules.autonomous_planner.plan_memory import PlanMemory
from layers.layer10_monetization.modules.autonomous_planner.planning_metrics import PlanningMetrics
from layers.layer10_monetization.modules.autonomous_planner.planning_report_generator import PlanningReportGenerator

_APM_COUNTER = itertools.count(1)


class AutonomousPlanningManager:
    """Complete autonomous planning pipeline.

    Flow: Goal → Decompose → Decide → Simulate → Plan Resources → Assess Risk
          → Adapt → Detect Opportunities → Store Memory → Metrics → Report
    """

    def __init__(self) -> None:
        self.planner = AutonomousPlanner()
        self.decomposer = GoalDecomposer()
        self.decision_matrix = DecisionMatrix()
        self.simulator = ScenarioSimulator()
        self.resource_planner = ResourcePlanner()
        self.risk_manager = RiskManager()
        self.adaptive_planner = AdaptivePlanner()
        self.opportunity_detector = OpportunityDetector()
        self.plan_memory = PlanMemory()
        self.metrics = PlanningMetrics()
        self.report_generator = PlanningReportGenerator()
        self._pipeline_runs: List[Dict[str, Any]] = []

    def plan(self, goal: str, goal_type: str = "",
             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        context = context or {}
        results: Dict[str, Any] = {"goal": goal, "stages": {}}

        # Stage 1: Decompose goal
        decomposition = self.decomposer.decompose(goal, goal_type)
        results["stages"]["decompose"] = decomposition.to_dict()

        # Stage 2: Decision matrix — evaluate approaches
        for approach in ["conservative", "balanced", "aggressive"]:
            option = self.decision_matrix.add_option(approach)
            if approach == "conservative":
                option.set_score("impact", 0.4); option.set_score("risk", 0.2)
                option.set_score("confidence", 0.8); option.set_score("cost", 0.3)
            elif approach == "balanced":
                option.set_score("impact", 0.6); option.set_score("risk", 0.4)
                option.set_score("confidence", 0.7); option.set_score("cost", 0.5)
            else:
                option.set_score("impact", 0.9); option.set_score("risk", 0.7)
                option.set_score("confidence", 0.5); option.set_score("cost", 0.8)
        best_approach = self.decision_matrix.evaluate()
        results["stages"]["decision"] = best_approach.to_dict() if best_approach else {}

        # Stage 3: Simulate scenarios
        layers = []
        for ms in decomposition.milestones:
            for task in ms.tasks:
                if task.get("layer") and task["layer"] not in layers:
                    layers.append(task["layer"])

        scenario = self.simulator.create_scenario("primary_plan",
            [{"layer": l, "action": "execute"} for l in layers])
        self.simulator.simulate(scenario.scenario_id)
        results["stages"]["simulation"] = scenario.to_dict()

        # Stage 4: Resource planning
        resource_plan = self.resource_planner.plan_for_layers(layers)
        results["stages"]["resources"] = resource_plan.to_dict()

        # Stage 5: Risk assessment
        risks = self.risk_manager.detect_risks(layers, context)
        results["stages"]["risks"] = {"count": len(risks),
                                       "high": len(self.risk_manager.get_high_risks())}

        # Stage 6: Create autonomous plan
        steps = []
        for ms in decomposition.milestones:
            for task in ms.tasks:
                steps.append({"layer": task.get("layer", ""), "action": task.get("action", "")})
        plan = self.planner.create_plan(goal, steps)
        results["stages"]["plan"] = plan.to_dict()

        # Stage 7: Detect opportunities
        opportunities = self.opportunity_detector.scan(context)
        results["stages"]["opportunities"] = {"count": len(opportunities)}

        # Stage 8: Store in memory
        self.plan_memory.store(
            plan_type=goal_type, goal=goal, steps_count=len(steps),
            success=True, duration_ms=(time.time() - start) * 1000,
        )

        # Stage 9: Record metrics
        self.metrics.record_plan(
            success=True, execution_time_ms=(time.time() - start) * 1000,
            resource_efficiency=0.7, decision_score=best_approach.total_score if best_approach else 0,
        )

        # Stage 10: Generate report
        report = self.report_generator.generate("planning", results)
        report.add_recommendation(f"Proceed with {best_approach.name} approach" if best_approach else "Review plan")

        results["plan_id"] = plan.plan_id
        results["report_id"] = report.report_id
        results["duration_ms"] = round((time.time() - start) * 1000, 1)
        results["ready_for_execution"] = True

        self._pipeline_runs.append(results)
        return results

    def adapt_plan(self, plan_id: str, trigger: str,
                   data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if trigger == "failure":
            event = self.adaptive_planner.adapt_on_failure(
                plan_id, data.get("layer", ""), data.get("error", ""))
        elif trigger == "analytics":
            event = self.adaptive_planner.adapt_on_analytics(
                plan_id, data.get("metric", ""), data.get("value", 0.0))
        elif trigger == "timeout":
            event = self.adaptive_planner.adapt_on_timeout(plan_id, data.get("layer", ""))
        else:
            return {"status": "unknown_trigger"}
        return event.to_dict()

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_plans": self.planner.get_stats()["total_plans"],
            "total_decompositions": self.decomposer.get_stats()["total_decompositions"],
            "total_risks": self.risk_manager.get_stats()["total_risks"],
            "total_adaptations": self.adaptive_planner.get_stats()["total_adaptations"],
            "metrics": self.metrics.get_summary(),
            "memory": self.plan_memory.get_stats(),
        }

    def get_recent_results(self, count: int = 5) -> List[Dict[str, Any]]:
        return list(self._pipeline_runs[-count:])
