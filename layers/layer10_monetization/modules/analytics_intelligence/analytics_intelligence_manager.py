"""AnalyticsIntelligenceManager — Orchestrate the full analytics pipeline."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.analytics_intelligence.analytics_profile import AnalyticsProfile
from layers.layer10_monetization.modules.analytics_intelligence.analytics_collector import AnalyticsCollector
from layers.layer10_monetization.modules.analytics_intelligence.analytics_normalizer import AnalyticsNormalizer
from layers.layer10_monetization.modules.analytics_intelligence.trend_analyzer import TrendAnalyzer
from layers.layer10_monetization.modules.analytics_intelligence.content_optimizer import ContentOptimizer
from layers.layer10_monetization.modules.analytics_intelligence.engagement_predictor import EngagementPredictor
from layers.layer10_monetization.modules.analytics_intelligence.timing_optimizer import TimingOptimizer
from layers.layer10_monetization.modules.analytics_intelligence.audience_insight import AudienceInsight
from layers.layer10_monetization.modules.analytics_intelligence.performance_scorer import PerformanceScorer
from layers.layer10_monetization.modules.analytics_intelligence.analytics_memory import AnalyticsMemory
from layers.layer10_monetization.modules.analytics_intelligence.analytics_report import AnalyticsReportGenerator


class AnalyticsIntelligenceManager:
    """Full analytics intelligence pipeline.

    Flow: Collect → Normalize → Analyze Trends → Optimize Content →
          Optimize Timing → Audience Insight → Score → Predict →
          Store → Report
    """

    def __init__(self) -> None:
        self.collector = AnalyticsCollector()
        self.normalizer = AnalyticsNormalizer()
        self.trend_analyzer = TrendAnalyzer()
        self.content_optimizer = ContentOptimizer()
        self.engagement_predictor = EngagementPredictor()
        self.timing_optimizer = TimingOptimizer()
        self.audience_insight = AudienceInsight()
        self.performance_scorer = PerformanceScorer()
        self.memory = AnalyticsMemory()
        self.report_generator = AnalyticsReportGenerator()
        self._is_running = False

    def start(self) -> bool:
        self._is_running = True
        return True

    def stop(self) -> bool:
        self._is_running = False
        return True

    def collect_analytics(self, platform: str, post_id: str,
                          data: Optional[Dict[str, Any]] = None) -> AnalyticsProfile:
        profile = self.collector.collect(platform, post_id, data)
        self.normalizer.normalize(platform, data or {})
        score = self.performance_scorer.score(profile)
        self.memory.store(platform, post_id, {"score": score.normalized_score},
                          score=score.normalized_score)
        return profile

    def analyze_trends(self, platform: str, metric_name: str,
                       values: List[float]) -> Dict[str, Any]:
        pattern = self.trend_analyzer.analyze(metric_name, values, platform)
        return pattern.to_dict()

    def predict_engagement(self, topic: str, platform: str,
                           historical: float = 0.0) -> Dict[str, Any]:
        pred = self.engagement_predictor.predict(topic, platform, historical)
        return pred.to_dict()

    def optimize_content(self, platform: str, content_type: str,
                         metrics: Dict[str, float]) -> Dict[str, Any]:
        insights = self.content_optimizer.analyze_content(platform, content_type, metrics)
        return {"insights": [i.to_dict() for i in insights],
                "count": len(insights)}

    def find_best_times(self, platform: str = "",
                        count: int = 5) -> List[Dict[str, Any]]:
        slots = self.timing_optimizer.get_best_times(platform, count)
        return [s.to_dict() for s in slots]

    def generate_report(self, report_type: str = "daily",
                        data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        report = self.report_generator.generate(report_type, data or {})
        return report.to_dict()

    def get_health(self) -> Dict[str, Any]:
        return {
            "collector": self.collector.get_stats(),
            "normalizer": self.normalizer.get_stats(),
            "trend_analyzer": self.trend_analyzer.get_stats(),
            "content_optimizer": self.content_optimizer.get_stats(),
            "engagement_predictor": self.engagement_predictor.get_stats(),
            "timing_optimizer": self.timing_optimizer.get_stats(),
            "audience_insight": self.audience_insight.get_stats(),
            "performance_scorer": self.performance_scorer.get_stats(),
            "memory": self.memory.get_stats(),
            "report_generator": self.report_generator.get_stats(),
            "is_running": self._is_running,
        }

    def run_full_pipeline(self, platform: str, post_id: str,
                          data: Optional[Dict[str, Any]] = None,
                          topic: str = "") -> Dict[str, Any]:
        start = time.time()
        results: Dict[str, Any] = {"topic": topic or post_id, "platform": platform}

        profile = self.collect_analytics(platform, post_id, data)

        score = self.performance_scorer.score(profile)
        results["score"] = score.to_dict()

        if topic:
            pred = self.engagement_predictor.predict(topic, platform)
            results["prediction"] = pred.to_dict()

        results["content_insights"] = self.content_optimizer.analyze_content(
            platform, profile.content_type,
            {"engagement_rate": profile.engagement_rate, "ctr": profile.ctr, "reach": profile.reach})

        report = self.report_generator.generate("pipeline", results)
        results["report"] = report.to_dict()
        results["duration_ms"] = round((time.time() - start) * 1000, 1)
        return results
