"""Quality Orchestrator — production Layer 06 quality pipeline."""
from __future__ import annotations

import itertools
import time
from typing import Any, Callable, Dict, List, Mapping, Optional

from layers.layer06_quality.modules.brand_voice_engine.brand_voice_engine import BrandVoiceEngine
from layers.layer06_quality.modules.content_quality_analyzer.quality_analyzer import ContentQualityAnalyzer
from layers.layer06_quality.modules.fact_citation_validator.fact_validator import FactValidator
from layers.layer06_quality.modules.plagiarism_originality_engine.plagiarism_engine import PlagiarismEngine
from layers.layer06_quality.modules.platform_compliance_engine.compliance_engine import ComplianceEngine
from layers.layer06_quality.modules.quality_orchestrator.pipeline_runner import PipelineRunner
from layers.layer06_quality.modules.quality_orchestrator.quality_report import (
    ModuleExecutionRecord,
    QualityReport,
)
from layers.layer06_quality.modules.quality_scoring_engine.quality_engine import QualityEngine
from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore
from layers.layer06_quality.modules.safety_policy_checker.safety_engine import SafetyEngine
from layers.layer06_quality.modules.seo_discoverability_engine.seo_engine import SEOEngine


_COUNTER = itertools.count(1)


class QualityOrchestrator:
    """Run the complete Layer 06 quality pipeline.

    Production runs always use real Layer 06 engines by default. A caller may
    inject module functions for controlled tests/integrations, but missing
    required modules are represented as failures rather than simulated scores.
    """

    def __init__(
        self,
        pipeline_runner: Optional[PipelineRunner] = None,
        quality_engine: Optional[QualityEngine] = None,
        content_quality: Optional[ContentQualityAnalyzer] = None,
        fact_validator: Optional[FactValidator] = None,
        safety_engine: Optional[SafetyEngine] = None,
        plagiarism_engine: Optional[PlagiarismEngine] = None,
        seo_engine: Optional[SEOEngine] = None,
        compliance_engine: Optional[ComplianceEngine] = None,
        brand_voice_engine: Optional[BrandVoiceEngine] = None,
    ) -> None:
        self.runner = pipeline_runner or PipelineRunner()
        self.quality_engine = quality_engine or QualityEngine()
        self.content_quality = content_quality or ContentQualityAnalyzer()
        self.fact_validator = fact_validator or FactValidator()
        self.safety_engine = safety_engine or SafetyEngine()
        self.plagiarism_engine = plagiarism_engine or PlagiarismEngine()
        self.seo_engine = seo_engine or SEOEngine()
        self.compliance_engine = compliance_engine or ComplianceEngine()
        self.brand_voice_engine = brand_voice_engine or BrandVoiceEngine()
        self._orchestration_count = 0
        self._history: List[QualityReport] = []

    def run(
        self,
        content: str,
        content_id: str = "",
        platform: str = "facebook",
        module_funcs: Optional[Mapping[str, Callable[..., Any]]] = None,
        layer2_confidence: float = 0.5,
        layer3_confidence: float = 0.5,
        keyword: str = "",
        title: str = "",
        description: str = "",
        evidence_texts: Optional[List[Dict[str, str]]] = None,
    ) -> QualityReport:
        """Run all required quality engines and return a deterministic report."""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")
        if not isinstance(platform, str) or not platform.strip():
            raise ValueError("platform must be a non-empty string")
        if not 0.0 <= layer2_confidence <= 1.0:
            raise ValueError("layer2_confidence must be between 0 and 1")
        if not 0.0 <= layer3_confidence <= 1.0:
            raise ValueError("layer3_confidence must be between 0 and 1")

        report = QualityReport(
            report_id=f"qr_{next(_COUNTER)}",
            content_id=content_id,
        )
        start_time = time.monotonic()
        events: List[Dict[str, Any]] = [
            {"event": "quality_started", "report_id": report.report_id},
        ]

        funcs = dict(module_funcs) if module_funcs is not None else self._default_module_funcs()
        records = self.runner.run_pipeline(
            funcs,
            {
                "content": content,
                "platform": platform,
                "keyword": keyword,
                "title": title,
                "description": description,
                "evidence_texts": evidence_texts,
            },
        )
        report.module_records = records

        module_scores = self._records_to_scores(records)
        quality_result = self.quality_engine.score(
            module_scores, layer2_confidence, layer3_confidence,
        )

        report.overall_score = quality_result.overall_score
        report.confidence = quality_result.confidence
        report.grade = quality_result.grade
        report.decision = quality_result.decision
        report.risk_level = quality_result.risk_level
        report.hard_stops = quality_result.hard_stops
        report.explanations = [e.to_dict() for e in quality_result.explanations]
        report.publish_readiness = min(
            1.0,
            quality_result.confidence * (quality_result.overall_score / 100.0),
        )
        report.total_duration_ms = round(
            (time.monotonic() - start_time) * 1000, 2,
        )

        events.append({
            "event": "quality_completed",
            "report_id": report.report_id,
            "decision": report.decision,
            "score": report.overall_score,
        })
        report.events = events
        report.metadata = {
            "platform": platform,
            "content_length": len(content),
            "modules_executed": sum(
                1 for r in records if r.status == "completed"
            ),
            "modules_failed": sum(1 for r in records if r.status == "failed"),
            "modules_skipped": sum(1 for r in records if r.status == "skipped"),
        }

        slowest = self.runner.get_slowest_modules(records)
        if slowest:
            report.metadata["slowest_module"] = slowest[0].module_name
            report.metadata["slowest_duration_ms"] = slowest[0].duration_ms

        self._history.append(report)
        self._orchestration_count += 1
        return report

    def _default_module_funcs(self) -> Dict[str, Callable[..., Any]]:
        """Build real engine adapters used by production runs."""
        return {
            "content_quality": self._run_content_quality,
            "fact_validation": self._run_fact_validation,
            "safety": self._run_safety,
            "originality": self._run_originality,
            "seo": self._run_seo,
            "platform_compliance": self._run_platform_compliance,
            "brand_voice": self._run_brand_voice,
        }

    def _run_content_quality(self, content: str, platform: str, **_: Any) -> Dict[str, Any]:
        result = self.content_quality.analyze(content, platform)
        return {
            "score": result.overall_score * 100,
            "confidence": 0.9 if not result.metadata.get("hard_gate_failures") else 0.25,
            "issues_count": len(result.issues),
        }

    def _run_fact_validation(
        self,
        content: str,
        evidence_texts: Optional[List[Dict[str, str]]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        result = self.fact_validator.validate(content, evidence_texts)
        status_confidence = {
            "verified": 0.9,
            "partially_verified": 0.65,
            "needs_review": 0.4,
            "mostly_unsupported": 0.2,
            "contradicted": 0.1,
            "no_claims": 0.5,
        }
        return {
            "score": result.overall_score * 100,
            "confidence": status_confidence.get(result.overall_status, 0.3),
            "issues_count": len(result.issues),
        }

    def _run_safety(self, content: str, platform: str, **_: Any) -> Dict[str, Any]:
        result = self.safety_engine.check(content, [platform])
        return {
            "score": result.overall_score * 100,
            "confidence": 0.95 if result.overall_safe else 0.8,
            "issues_count": len(result.flags),
        }

    def _run_originality(self, content: str, **_: Any) -> Dict[str, Any]:
        result = self.plagiarism_engine.check(content)
        return {
            "score": result.overall_originality_score * 100,
            "confidence": 0.85,
            "issues_count": len(result.flagged_segments) + len(result.self_plagiarism_matches),
        }

    def _run_seo(
        self,
        content: str,
        platform: str,
        keyword: str = "",
        title: str = "",
        description: str = "",
        **_: Any,
    ) -> Dict[str, Any]:
        result = self.seo_engine.check(
            content,
            keyword=keyword,
            title=title,
            description=description,
            platform=platform,
        )
        return {
            "score": result.overall_score * 100,
            "confidence": 0.8,
            "issues_count": len(result.issues),
        }

    def _run_platform_compliance(
        self, content: str, platform: str, **_: Any,
    ) -> Dict[str, Any]:
        result = self.compliance_engine.check(content, platform)
        return {
            "score": result.compliance_score * 100,
            "confidence": 0.95,
            "issues_count": len(result.violations),
        }

    def _run_brand_voice(self, content: str, **_: Any) -> Dict[str, Any]:
        result = self.brand_voice_engine.check(content)
        return {
            "score": result.overall_score * 100,
            "confidence": 0.75,
            "issues_count": len(result.issues),
        }

    def run_quick(self, content: str, platform: str = "facebook") -> Dict[str, Any]:
        """Run the production pipeline and return a compact summary."""
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
        return round(
            sum(r.overall_score for r in self._history) / len(self._history), 1,
        )

    def get_statistics(self) -> Dict[str, Any]:
        if not self._history:
            return {"total_runs": 0}
        return {
            "total_runs": len(self._history),
            "avg_score": self.get_average_score(),
            "avg_duration_ms": round(
                sum(r.total_duration_ms for r in self._history)
                / len(self._history),
                2,
            ),
            "decisions": {
                d: sum(1 for r in self._history if r.decision == d)
                for d in (
                    "approve",
                    "approve_with_warnings",
                    "human_review",
                    "revise",
                    "reject",
                )
            },
        }

    def _records_to_scores(
        self, records: List[ModuleExecutionRecord],
    ) -> List[ModuleScore]:
        scores: List[ModuleScore] = []
        for rec in records:
            if rec.status == "completed":
                scores.append(ModuleScore(
                    module_name=rec.module_name,
                    score=rec.score,
                    confidence=rec.confidence,
                ))
            elif rec.status == "failed":
                ms = ModuleScore(
                    module_name=rec.module_name,
                    score=0.0,
                    confidence=0.0,
                )
                ms.critical_issues.append(
                    f"Module failed: {rec.error_message[:100]}"
                )
                scores.append(ms)
        return scores

    @property
    def orchestration_count(self) -> int:
        return self._orchestration_count
