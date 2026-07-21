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
        """Real content quality analysis when no external modules provided."""
        import re
        content_len = len(content)
        word_count = len(content.split())
        
        records = []
        
        # 1. Content Quality — based on length, structure, readability
        length_score = min(100, max(0, (content_len / 50) * 10))
        has_paragraphs = "\n\n" in content or content_len > 200
        structure_score = 10 if has_paragraphs else 3
        quality_score = min(100, length_score + structure_score)
        rec = ModuleExecutionRecord("content_quality")
        rec.status = "completed"
        rec.score = round(quality_score, 1)
        rec.confidence = 0.8
        rec.duration_ms = 1.0
        records.append(rec)
        
        # 2. Safety — check for harmful content patterns
        harmful = ["kill", "hate", "attack", "bomb"]
        harmful_count = sum(1 for h in harmful if h in content.lower())
        safety_score = max(0, 100 - harmful_count * 20)
        rec = ModuleExecutionRecord("safety")
        rec.status = "completed"
        rec.score = safety_score
        rec.confidence = 0.9
        rec.duration_ms = 0.5
        records.append(rec)
        
        # 3. Originality — based on uniqueness markers
        unique_words = len(set(content.lower().split()))
        uniqueness = unique_words / max(word_count, 1) * 100
        rec = ModuleExecutionRecord("originality")
        rec.status = "completed"
        rec.score = round(min(100, uniqueness), 1)
        rec.confidence = 0.7
        rec.duration_ms = 0.5
        records.append(rec)
        
        # 4. SEO — keyword density, hashtag presence
        hashtags = len(re.findall(r"#\w+", content))
        mentions = len(re.findall(r"@\w+", content))
        seo_score = min(100, 40 + hashtags * 10 + mentions * 5)
        rec = ModuleExecutionRecord("seo")
        rec.status = "completed"
        rec.score = seo_score
        rec.confidence = 0.75
        rec.duration_ms = 0.5
        records.append(rec)
        
        # 5. Platform Compliance — Facebook specific
        platform_limits = {"facebook": 63206, "twitter": 280, "linkedin": 3000}
        limit = platform_limits.get(platform.lower(), 5000)
        compliance = 100 if content_len <= limit else max(0, 100 - ((content_len - limit) / limit * 100))
        rec = ModuleExecutionRecord("platform_compliance")
        rec.status = "completed"
        rec.score = round(compliance, 1)
        rec.confidence = 0.95
        rec.duration_ms = 0.3
        records.append(rec)
        
        # 6. Brand Voice — CTA and engagement markers
        cta_words = ["follow", "like", "share", "comment", "subscribe", "click"]
        cta_count = sum(1 for c in cta_words if c in content.lower())
        emoji_count = len(re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]", content))
        brand_score = min(100, 50 + cta_count * 10 + emoji_count * 5)
        rec = ModuleExecutionRecord("brand_voice")
        rec.status = "completed"
        rec.score = brand_score
        rec.confidence = 0.7
        rec.duration_ms = 0.5
        records.append(rec)
        
        # Quality scoring record
        avg_score = sum(r.score for r in records) / len(records)
        scoring_rec = ModuleExecutionRecord("quality_scoring")
        scoring_rec.status = "completed"
        scoring_rec.score = round(avg_score, 1)
        scoring_rec.confidence = 0.85
        scoring_rec.duration_ms = 1.0
        records.append(scoring_rec)
        
        return records

    @property
    def orchestration_count(self) -> int:
        return self._orchestration_count
