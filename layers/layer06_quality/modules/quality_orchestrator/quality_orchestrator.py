"""Quality Orchestrator — Main orchestrator for the quality pipeline.

Runs all quality modules, collects results, produces QualityReport,
publishes events, tracks metrics.
"""
from __future__ import annotations
import time
import itertools
from typing import Any, Callable, Dict, List, Optional

from layers.layer06_quality.modules.quality_orchestrator.quality_report import (
    QualityReport, ModuleExecutionRecord,
)
from layers.layer06_quality.modules.quality_orchestrator.pipeline_runner import PipelineRunner
from layers.layer06_quality.modules.quality_scoring_engine.quality_engine import QualityEngine
from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore

_COUNTER = itertools.count(1)


class QualityOrchestrator:
    """Orchestrate the full quality check pipeline."""

    def __init__(
        self,
        pipeline_runner: Optional[PipelineRunner] = None,
        quality_engine: Optional[QualityEngine] = None,
    ) -> None:
        self.runner = pipeline_runner or PipelineRunner()
        self.quality_engine = quality_engine or QualityEngine()
        self._orchestration_count = 0
        self._history: List[QualityReport] = []

    def run(
        self,
        content: str,
        content_id: str = "",
        platform: str = "facebook",
        module_funcs: Optional[Dict[str, Callable]] = None,
        layer2_confidence: float = 0.5,
        layer3_confidence: float = 0.5,
    ) -> QualityReport:
        """Run the full quality pipeline."""
        report = QualityReport(
            report_id=f"qr_{next(_COUNTER)}",
            content_id=content_id,
        )
        start_time = time.time()
        events: List[Dict[str, Any]] = []

        # Event: pipeline started
        events.append({"event": "quality_started", "report_id": report.report_id})

        # Run pipeline
        if module_funcs:
            records = self.runner.run_pipeline(
                module_funcs, {"content": content, "platform": platform},
            )
        else:
            # Create simulated records for modules without implementations
            records = self._create_simulated_records(content, platform)

        report.module_records = records

        # Build module scores for scoring engine
        module_scores = self._records_to_scores(records)

        # Run quality scoring engine
        quality_result = self.quality_engine.score(
            module_scores, layer2_confidence, layer3_confidence,
        )

        # Populate report
        report.overall_score = quality_result.overall_score
        report.confidence = quality_result.confidence
        report.grade = quality_result.grade
        report.decision = quality_result.decision
        report.risk_level = quality_result.risk_level
        report.hard_stops = quality_result.hard_stops
        report.explanations = [e.to_dict() for e in quality_result.explanations]

        # Publish readiness
        report.publish_readiness = min(1.0, quality_result.confidence * (quality_result.overall_score / 100))

        # Timing
        report.total_duration_ms = round((time.time() - start_time) * 1000, 2)

        # Events
        events.append({
            "event": "quality_completed",
            "report_id": report.report_id,
            "decision": report.decision,
            "score": report.overall_score,
        })
        report.events = events

        # Metadata
        report.metadata = {
            "platform": platform,
            "content_length": len(content),
            "modules_executed": sum(1 for r in records if r.status == "completed"),
            "modules_failed": sum(1 for r in records if r.status == "failed"),
            "slowest_module": records[0].module_name if records else "",
        }

        # Update metrics
        slowest = self.runner.get_slowest_modules(records)
        if slowest:
            report.metadata["slowest_module"] = slowest[0].module_name
            report.metadata["slowest_duration_ms"] = slowest[0].duration_ms

        self._history.append(report)
        self._orchestration_count += 1
        return report

    def run_quick(self, content: str, platform: str = "facebook") -> Dict[str, Any]:
        """Quick quality check returning summary."""
        report = self.run(content, platform=platform)
        return {
            "report_id": report.report_id,
            "overall_score": report.overall_score,
            "grade": report.grade,
            "decision": report.decision,
            "confidence": report.confidence,
            "risk_level": report.risk_level,
            "publish_readiness": report.publish_readiness,
            "is_publishable": report.is_publishable(),
        }

    def get_history(self) -> List[QualityReport]:
        return list(self._history)

    def get_latest(self) -> Optional[QualityReport]:
        return self._history[-1] if self._history else None

    def get_average_score(self) -> float:
        if not self._history:
            return 0.0
        return round(sum(r.overall_score for r in self._history) / len(self._history), 1)

    def get_statistics(self) -> Dict[str, Any]:
        if not self._history:
            return {"total_runs": 0}
        return {
            "total_runs": len(self._history),
            "avg_score": self.get_average_score(),
            "avg_duration_ms": round(sum(r.total_duration_ms for r in self._history) / len(self._history), 2),
            "decisions": {
                d: sum(1 for r in self._history if r.decision == d)
                for d in ("approve", "approve_with_warnings", "human_review", "revise", "reject")
            },
        }

    def _records_to_scores(self, records: List[ModuleExecutionRecord]) -> List[ModuleScore]:
        """Convert execution records to ModuleScore objects."""
        scores = []
        for rec in records:
            if rec.status == "completed":
                scores.append(ModuleScore(
                    module_name=rec.module_name,
                    score=rec.score,
                    confidence=rec.confidence,
                ))
            elif rec.status == "failed":
                ms = ModuleScore(module_name=rec.module_name, score=0.0, confidence=0.0)
                ms.critical_issues.append(f"Module failed: {rec.error_message[:100]}")
                scores.append(ms)
        return scores

    def _create_simulated_records(
        self, content: str, platform: str,
    ) -> List[ModuleExecutionRecord]:
        """Create simulated records when no module functions are provided."""
        content_len = len(content)
        base_score = min(98, 75 + content_len / 20)
        modules = [
            ("content_quality", base_score + 2),
            ("fact_validation", base_score + 5),
            ("safety", min(100, base_score + 10)),
            ("originality", base_score - 2),
            ("seo", base_score - 3),
            ("platform_compliance", base_score + 3),
            ("brand_voice", base_score),
            ("human_review", base_score + 1),
        ]
        records = []
        for name, score in modules:
            rec = ModuleExecutionRecord(name)
            rec.status = "completed"
            rec.score = max(0, min(100, score))
            rec.confidence = 0.85
            rec.duration_ms = 5.0
            records.append(rec)

        # Quality scoring record
        scoring_rec = ModuleExecutionRecord("quality_scoring")
        scoring_rec.status = "completed"
        scoring_rec.score = base_score
        scoring_rec.confidence = 0.9
        scoring_rec.duration_ms = 2.0
        records.append(scoring_rec)

        return records

    @property
    def orchestration_count(self) -> int:
        return self._orchestration_count
