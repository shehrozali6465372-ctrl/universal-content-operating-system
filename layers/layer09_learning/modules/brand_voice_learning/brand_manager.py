"""Brand Manager — Orchestrate the full brand voice learning pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.brand_voice_learning.brand_profile import BrandProfile
from layers.layer09_learning.modules.brand_voice_learning.voice_analyzer import VoiceAnalyzer
from layers.layer09_learning.modules.brand_voice_learning.tone_learning import ToneLearner
from layers.layer09_learning.modules.brand_voice_learning.vocabulary_learning import VocabularyLearner
from layers.layer09_learning.modules.brand_voice_learning.style_learning import StyleLearner
from layers.layer09_learning.modules.brand_voice_learning.terminology_learning import TerminologyLearner
from layers.layer09_learning.modules.brand_voice_learning.consistency_tracker import ConsistencyTracker
from layers.layer09_learning.modules.brand_voice_learning.brand_memory import BrandMemory
from layers.layer09_learning.modules.brand_voice_learning.voice_metrics import VoiceMetrics

_BMGR_COUNTER = itertools.count(1)


class BrandCycleResult:
    """Result of a full brand voice learning cycle."""

    __slots__ = (
        "cycle_id", "brand_id", "voice_analysis", "tone_insights",
        "vocabulary_insights", "style_insights", "consistency_score",
        "violations_found", "recommendations", "timestamp", "duration_ms",
    )

    def __init__(self, brand_id: str = "") -> None:
        self.cycle_id: str = f"bcy_{next(_BMGR_COUNTER)}"
        self.brand_id = brand_id
        self.voice_analysis = None
        self.tone_insights: List[Dict[str, Any]] = []
        self.vocabulary_insights: List[Dict[str, Any]] = []
        self.style_insights: List[Dict[str, Any]] = []
        self.consistency_score: float = 0.0
        self.violations_found: int = 0
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "brand_id": self.brand_id,
            "tone_insight_count": len(self.tone_insights),
            "vocabulary_insight_count": len(self.vocabulary_insights),
            "style_insight_count": len(self.style_insights),
            "consistency_score": round(self.consistency_score, 3),
            "violations_found": self.violations_found,
            "recommendation_count": len(self.recommendations),
            "duration_ms": round(self.duration_ms, 1),
        }


class BrandManager:
    """Orchestrate the full brand voice learning pipeline.

    Flow: Analyze → Learn Tones → Learn Vocabulary → Learn Style → Check Consistency → Store
    """

    def __init__(self) -> None:
        self.analyzer = VoiceAnalyzer()
        self.tone_learner = ToneLearner()
        self.vocabulary_learner = VocabularyLearner()
        self.style_learner = StyleLearner()
        self.terminology_learner = TerminologyLearner()
        self.consistency_tracker = ConsistencyTracker()
        self.memory = BrandMemory()
        self.metrics = VoiceMetrics()
        self._brands: List[BrandProfile] = []
        self._cycles: List[BrandCycleResult] = []
        self._events: List[Dict[str, Any]] = []

    def register_brand(self, brand: BrandProfile) -> None:
        self._brands.append(brand)

    def run_learning_cycle(
        self,
        brand: BrandProfile,
        content_samples: List[str],
        tone_performance: Optional[Dict[str, List[float]]] = None,
        vocabulary_performance: Optional[Dict[str, List[float]]] = None,
        style_performance: Optional[Dict[str, Dict[str, List[float]]]] = None,
    ) -> BrandCycleResult:
        start = time.time()
        result = BrandCycleResult(brand.profile_id)

        # Step 1: Analyze voice from samples
        for sample in content_samples:
            analysis = self.analyzer.analyze(sample)
            self.metrics.record_analysis()
        result.voice_analysis = self.analyzer.get_results()[-1] if self.analyzer.get_results() else None

        # Step 2: Learn tones
        if tone_performance:
            tone_insights = self.tone_learner.learn(brand.tone_profile, tone_performance)
            result.tone_insights = [t.to_dict() for t in tone_insights]
            self.metrics.record_tone_adjustment()

        # Step 3: Learn vocabulary
        if vocabulary_performance:
            vocab_insights = self.vocabulary_learner.learn(
                brand.vocabulary_preferences, vocabulary_performance,
            )
            result.vocabulary_insights = [v.to_dict() for v in vocab_insights]
            self.metrics.record_vocabulary_adjustment()

        # Step 4: Learn style
        if style_performance:
            current_style = {
                "sentence_style": brand.sentence_style,
                "paragraph_style": brand.paragraph_style,
                "emoji_style": brand.emoji_style,
                "cta_style": brand.cta_style,
                "hashtag_style": brand.hashtag_style,
            }
            style_insights = self.style_learner.learn(current_style, style_performance)
            result.style_insights = [s.to_dict() for s in style_insights]

        # Step 5: Check consistency
        for sample in content_samples[:3]:
            check = self.consistency_tracker.check_content(sample, brand)
            self.metrics.record_consistency_check(
                check.overall_score, len(check.violations),
            )
        result.consistency_score = self.consistency_tracker.get_average_score()
        result.violations_found = self.consistency_tracker.get_violations_count()

        # Step 6: Generate recommendations
        result.recommendations = self._generate_recommendations(brand, result)

        # Step 7: Store learnings
        if result.tone_insights or result.vocabulary_insights:
            self.memory.store(
                brand.profile_id, "learning_cycle",
                f"Cycle: {len(result.tone_insights)} tone, {len(result.vocabulary_insights)} vocab insights",
                confidence=result.consistency_score,
                tags=[brand.industry],
            )

        result.duration_ms = (time.time() - start) * 1000
        self._cycles.append(result)
        self._events.append({
            "event": "brand_cycle_completed",
            "cycle_id": result.cycle_id,
            "brand_id": brand.profile_id,
            "consistency": result.consistency_score,
        })
        return result

    def check_content(self, content: str, brand: BrandProfile,
                      platform: str = "") -> Dict[str, Any]:
        check = self.consistency_tracker.check_content(content, brand, platform)
        self.metrics.record_consistency_check(check.overall_score, len(check.violations))
        return check.to_dict()

    def _generate_recommendations(self, brand: BrandProfile, result: BrandCycleResult) -> List[str]:
        recs = []
        if result.consistency_score < 0.5:
            recs.append("Improve overall brand voice consistency")
        if result.violations_found > 0:
            recs.append(f"Fix {result.violations_found} brand voice violations")
        best_tones = self.tone_learner.get_best_tones(1)
        if best_tones:
            recs.append(f"Emphasize '{best_tones[0].tone}' tone (best performer)")
        return recs

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._cycles),
            "registered_brands": len(self._brands),
            "memory_stats": self.memory.get_stats(),
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_cycles(self, count: int = 5) -> List[BrandCycleResult]:
        return list(self._cycles[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)
