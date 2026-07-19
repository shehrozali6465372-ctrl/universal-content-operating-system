"""EvalOrchestrator — full evaluation pipeline."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from .quality_checker import QualityChecker
from .accuracy_checker import AccuracyChecker
from .hallucination_detector import HallucinationDetector
from .bias_detector import BiasDetector
from .safety_checker import SafetyChecker
from .grammar_checker import GrammarChecker
from .seo_checker import SEOChecker
from .creativity_checker import CreativityChecker
from .consistency_checker import ConsistencyChecker
from .brand_voice_checker import BrandVoiceChecker
from .eval_config import EvalConfig
from .eval_metrics import EvalMetrics
from .eval_events import EvalEvents
from .eval_health import EvalHealth
from .eval_validator import EvalValidator
from .models import EvalResult

class EvalOrchestrator:
    def __init__(self, config: Optional[EvalConfig] = None) -> None:
        self.config = config or EvalConfig()
        self.quality = QualityChecker(self.config.min_quality_score)
        self.accuracy = AccuracyChecker(self.config.min_accuracy)
        self.hallucination = HallucinationDetector()
        self.bias = BiasDetector()
        self.safety = SafetyChecker()
        self.grammar = GrammarChecker()
        self.seo = SEOChecker()
        self.creativity = CreativityChecker()
        self.consistency = ConsistencyChecker()
        self.brand_voice = BrandVoiceChecker()
        self.metrics = EvalMetrics()
        self.events = EvalEvents()
        self.health = EvalHealth()
        self.validator = EvalValidator()
        self._is_running = False
    def start(self) -> bool:
        self._is_running = True; self.events.publish("started"); return True
    def stop(self) -> bool:
        self._is_running = False; self.events.publish("stopped"); return True
    def evaluate(self, content: str, eval_types: Optional[List[str]] = None) -> Dict[str, Any]:
        start = time.time()
        validation = self.validator.validate_content(content)
        if not validation["valid"]:
            return {"valid": False, "issues": validation["issues"], "results": []}
        eval_types = eval_types or ["quality", "accuracy", "safety", "grammar"]
        results: List[EvalResult] = []
        checker_map = {"quality": self.quality, "accuracy": self.accuracy,
                       "hallucination": self.hallucination, "bias": self.bias,
                       "safety": self.safety, "grammar": self.grammar,
                       "seo": self.seo, "creativity": self.creativity,
                       "consistency": self.consistency, "brand_voice": self.brand_voice}
        for et in eval_types:
            checker = checker_map.get(et)
            if checker:
                result = checker.check(content)
                results.append(result)
                self.metrics.record(result.eval_type.value, result.score, result.passed)
        elapsed = (time.time() - start) * 1000
        avg_score = sum(r.score for r in results) / max(len(results), 1)
        all_passed = all(r.passed for r in results)
        return {"valid": True, "results": [r.to_dict() for r in results],
                "avg_score": round(avg_score, 4), "all_passed": all_passed,
                "evaluations": len(results), "latency_ms": round(elapsed, 2)}
    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()
    def get_stats(self) -> Dict[str, Any]:
        return self.metrics.to_dict()
