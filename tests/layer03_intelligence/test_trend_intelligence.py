"""Tests for Layer 3, Module 2: Trend Intelligence."""
from layers.layer03_intelligence.modules.trend_intelligence import (
    TrendManager, TrendCollector, TrendNormalizer, MomentumAnalyzer,
    LifecycleDetector, SeasonalityAnalyzer, ViralityPredictor,
    CrossPlatformFusion, TrendConfidence, TrendExplainer, TrendPredictor,
)
from layers.layer03_intelligence.modules.trend_intelligence.trend_evidence import (
    TrendEvidence, TrendEvidenceBuilder,
)
from layers.layer03_intelligence.modules.trend_intelligence.trend_history import (
    TrendHistory,
)
from layers.layer03_intelligence.modules.trend_intelligence.trend_events import (
    TrendEventBus, TrendEventEmitter, TrendEvent,
)


# ── TrendCollector ──────────────────────────────────────────────────

class TestTrendCollector:
    def setup_method(self):
        self.collector = TrendCollector()

    def test_collect_single(self):
        entry = self.collector.collect("AI", "google_trends", score=85, volume=5000)
        assert entry.topic == "AI"
        assert entry.score == 85
        assert self.collector.count() == 1

    def test_collect_dedup(self):
        e1 = self.collector.collect("AI", "google_trends", score=85, timestamp=1000.0)
        e2 = self.collector.collect("AI", "google_trends", score=85, timestamp=1000.0)
        assert e1.entry_id == e2.entry_id
        assert self.collector.count() == 1

    def test_collect_batch(self):
        entries = [{"topic": "AI", "source": "twitter", "score": 70}]
        results = self.collector.collect_batch(entries)
        assert len(results) == 1

    def test_get_topics(self):
        self.collector.collect("AI", "twitter", 70)
        self.collector.collect("Crypto", "reddit", 90)
        topics = self.collector.get_topics()
        assert "AI" in topics
        assert "Crypto" in topics

    def test_get_entries_filter(self):
        self.collector.collect("AI", "twitter", 70)
        self.collector.collect("AI", "reddit", 80)
        self.collector.collect("Crypto", "twitter", 90)
        assert len(self.collector.get_entries(source="twitter")) == 2
        assert len(self.collector.get_entries(topic="Crypto")) == 1

    def test_to_dict(self):
        self.collector.collect("AI", "twitter", 70)
        d = self.collector.to_dict()
        assert d["count"] == 1
        assert len(d["entries"]) == 1

    def test_clear(self):
        self.collector.collect("AI", "twitter", 70)
        self.collector.clear()
        assert self.collector.count() == 0

    def test_entry_id(self):
        e1 = self.collector.collect("AI", "twitter", 70)
        assert len(e1.entry_id) == 16


# ── TrendNormalizer ────────────────────────────────────────────────

class TestTrendNormalizer:
    def setup_method(self):
        self.normalizer = TrendNormalizer()

    def test_normalize_single_source(self):
        result = self.normalizer.normalize("AI", [{"source": "twitter", "score": 80}])
        assert result.topic == "AI"
        assert result.source_count == 1
        assert result.normalized_score > 0

    def test_normalize_multi_source(self):
        scores = [
            {"source": "twitter", "score": 80},
            {"source": "reddit", "score": 70},
            {"source": "google_trends", "score": 90},
        ]
        result = self.normalizer.normalize("AI", scores)
        assert result.source_count == 3
        assert result.normalized_score > 0

    def test_normalize_empty(self):
        result = self.normalizer.normalize("AI", [])
        assert result.source_count == 0

    def test_source_agreement(self):
        scores = [
            {"source": "twitter", "score": 80},
            {"source": "reddit", "score": 81},
        ]
        result = self.normalizer.normalize("AI", scores)
        assert result.source_agreement > 0.5

    def test_normalize_batch(self):
        trends = {"AI": [{"source": "twitter", "score": 80}]}
        results = self.normalizer.normalize_batch(trends)
        assert len(results) == 1

    def test_set_source_weight(self):
        self.normalizer.set_source_weight("custom", 0.95)
        assert self.normalizer.get_weights()["custom"] == 0.95


# ── MomentumAnalyzer ───────────────────────────────────────────────

class TestMomentumAnalyzer:
    def setup_method(self):
        self.analyzer = MomentumAnalyzer()

    def test_rising_momentum(self):
        result = self.analyzer.analyze([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result.direction == "rising"
        assert result.velocity > 0

    def test_falling_momentum(self):
        result = self.analyzer.analyze([5.0, 4.0, 3.0, 2.0, 1.0])
        assert result.direction == "falling"

    def test_stable_momentum(self):
        result = self.analyzer.analyze([3.0, 3.0, 3.0, 3.0])
        assert result.direction == "stable"

    def test_single_point(self):
        result = self.analyzer.analyze([5.0])
        assert result.velocity == 0.0

    def test_empty(self):
        result = self.analyzer.analyze([])
        assert result.velocity == 0.0

    def test_momentum_score_range(self):
        result = self.analyzer.analyze([1, 3, 5, 7, 9])
        assert -1.0 <= result.momentum_score <= 1.0

    def test_stability(self):
        result = self.analyzer.analyze([1, 1.01, 0.99, 1.005])
        assert result.stability > 0.5

    def test_to_dict(self):
        result = self.analyzer.analyze([1, 2, 3])
        d = result.to_dict()
        assert "velocity" in d
        assert "direction" in d

    def test_with_timestamps(self):
        data = [{"timestamp": 1, "score": 10}, {"timestamp": 2, "score": 20}]
        result = self.analyzer.analyze_with_timestamps(data)
        assert result.direction == "rising"


# ── LifecycleDetector ──────────────────────────────────────────────

class TestLifecycleDetector:
    def setup_method(self):
        self.detector = LifecycleDetector()

    def test_emerging(self):
        result = self.detector.detect([1, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08])
        assert result.stage in ("emerging", "growing")

    def test_growing(self):
        result = self.detector.detect([1, 2, 4, 8, 16])
        assert result.stage in ("growing", "peak")

    def test_peak(self):
        result = self.detector.detect([1, 5, 10, 10, 9])
        assert result.stage in ("peak", "growing")

    def test_declining(self):
        result = self.detector.detect([10, 8, 5, 3, 1])
        assert result.stage in ("declining", "dead")

    def test_short_data(self):
        result = self.detector.detect([1, 2])
        assert result.stage == "emerging"
        assert result.confidence < 0.5

    def test_to_dict(self):
        result = self.detector.detect([1, 2, 3, 4, 5])
        d = result.to_dict()
        assert "stage" in d
        assert "confidence" in d


# ── SeasonalityAnalyzer ────────────────────────────────────────────

class TestSeasonalityAnalyzer:
    def setup_method(self):
        self.analyzer = SeasonalityAnalyzer()

    def test_insufficient_data(self):
        result = self.analyzer.detect("AI", [{"timestamp": i, "score": i} for i in range(5)])
        assert result.pattern_type == "insufficient_data"

    def test_detect_weekly(self):
        # Create weekly pattern
        data = [{"timestamp": i, "score": 50 + 30 * (i % 7 == 0)} for i in range(28)]
        result = self.analyzer.detect("AI", data)
        assert result.period_days in (7, 0)

    def test_no_pattern(self):
        import random
        random.seed(42)
        data = [{"timestamp": i, "score": random.random()} for i in range(50)]
        result = self.analyzer.detect("AI", data)
        assert result.pattern_type in ("none", "weekly", "monthly", "yearly")

    def test_to_dict(self):
        data = [{"timestamp": i, "score": i % 7} for i in range(30)]
        result = self.analyzer.detect("AI", data)
        d = result.to_dict()
        assert "period_days" in d


# ── ViralityPredictor ──────────────────────────────────────────────

class TestViralityPredictor:
    def setup_method(self):
        self.predictor = ViralityPredictor()

    def test_high_virality(self):
        result = self.predictor.predict("AI", {
            "velocity": 90, "engagement_rate": 0.8, "share_count": 5000,
            "comment_count": 1000, "growth_rate": 15, "hours_since_peak": 2,
        })
        assert result.virality_score > 0.5
        assert result.risk_level in ("medium", "high")

    def test_low_virality(self):
        result = self.predictor.predict("AI", {
            "velocity": 5, "engagement_rate": 0.01, "share_count": 10,
            "comment_count": 5, "growth_rate": 0.1, "hours_since_peak": 100,
        })
        assert result.virality_score < 0.5
        assert result.risk_level == "low"

    def test_viral_probability_range(self):
        result = self.predictor.predict("AI", {"velocity": 50})
        assert 0.0 <= result.viral_probability <= 1.0

    def test_explanation(self):
        result = self.predictor.predict("AI", {"velocity": 80, "engagement_rate": 0.7})
        assert result.explanation != ""

    def test_to_dict(self):
        result = self.predictor.predict("AI", {"velocity": 50})
        d = result.to_dict()
        assert "virality_score" in d


# ── CrossPlatformFusion ────────────────────────────────────────────

class TestCrossPlatformFusion:
    def setup_method(self):
        self.fusion = CrossPlatformFusion()

    def test_fuse_single_platform(self):
        result = self.fusion.fuse("AI", {"twitter": 0.8})
        assert result.platform_count == 1
        assert result.fused_score > 0

    def test_fuse_multi_platform(self):
        result = self.fusion.fuse("AI", {"twitter": 0.8, "reddit": 0.7, "google_trends": 0.9})
        assert result.platform_count == 3
        assert result.consensus_level > 0.5

    def test_fuse_empty(self):
        result = self.fusion.fuse("AI", {})
        assert result.platform_count == 0

    def test_dominant_platform(self):
        result = self.fusion.fuse("AI", {"twitter": 0.9, "reddit": 0.3})
        assert result.dominant_platform == "twitter"

    def test_fuse_batch(self):
        trends = {"AI": {"twitter": 0.8}, "Crypto": {"reddit": 0.7}}
        results = self.fusion.fuse_batch(trends)
        assert len(results) == 2

    def test_find_cross_platform(self):
        t1 = self.fusion.fuse("AI", {"twitter": 0.8, "reddit": 0.7, "google_trends": 0.9})
        t2 = self.fusion.fuse("Crypto", {"twitter": 0.1})
        found = self.fusion.find_cross_platform_trends([t1, t2], min_platforms=2, min_score=0.3)
        assert len(found) == 1

    def test_to_dict(self):
        result = self.fusion.fuse("AI", {"twitter": 0.8})
        d = result.to_dict()
        assert "platform_count" in d


# ── TrendConfidence ────────────────────────────────────────────────

class TestTrendConfidence:
    def setup_method(self):
        self.tc = TrendConfidence()

    def test_high_confidence(self):
        result = self.tc.calculate("AI", {
            "data_points": 15, "source_count": 5, "hours_since_latest": 1, "score_variance": 0.05,
        })
        assert result.overall_confidence > 0.7
        assert result.risk_level == "low"

    def test_low_confidence(self):
        result = self.tc.calculate("AI", {
            "data_points": 1, "source_count": 1, "hours_since_latest": 200, "score_variance": 0.9,
        })
        assert result.overall_confidence < 0.4
        assert result.risk_level == "high"

    def test_to_dict(self):
        result = self.tc.calculate("AI", {"data_points": 5})
        d = result.to_dict()
        assert "overall_confidence" in d


# ── TrendExplainer ─────────────────────────────────────────────────

class TestTrendExplainer:
    def setup_method(self):
        self.explainer = TrendExplainer()

    def test_explain_with_signals(self):
        result = self.explainer.explain("AI", {
            "momentum": {"velocity": 0.8},
            "lifecycle": {"stage": "emerging"},
            "platforms": {"platform_count": 4},
            "virality": {"viral_probability": 0.8},
        })
        assert len(result.factors) > 0
        assert result.summary != ""

    def test_explain_risks(self):
        result = self.explainer.explain("AI", {
            "lifecycle": {"stage": "declining"},
            "competition": {"level": "high"},
        })
        assert len(result.risk_warnings) > 0

    def test_explain_minimal(self):
        result = self.explainer.explain("AI", {})
        assert result.summary != ""

    def test_to_dict(self):
        result = self.explainer.explain("AI", {"momentum": {"velocity": 0.8}})
        d = result.to_dict()
        assert "factors" in d


# ── TrendPredictor ─────────────────────────────────────────────────

class TestTrendPredictor:
    def setup_method(self):
        self.predictor = TrendPredictor()

    def test_rising_prediction(self):
        result = self.predictor.predict("AI", [1, 2, 3, 4, 5, 6, 7])
        assert result.predicted_direction == "rising"
        assert result.predicted_score > 0

    def test_falling_prediction(self):
        result = self.predictor.predict("AI", [7, 6, 5, 4, 3, 2, 1])
        assert result.predicted_direction == "falling"

    def test_insufficient_data(self):
        result = self.predictor.predict("AI", [1, 2])
        assert result.confidence == 0.0

    def test_confidence_range(self):
        result = self.predictor.predict("AI", [1, 3, 5, 7, 9, 11])
        assert 0.0 <= result.confidence <= 1.0

    def test_decay(self):
        result = self.predictor.predict_with_decay("AI", [1, 2, 3, 4, 5], decay_rate=0.5)
        assert result.predicted_score >= 0

    def test_to_dict(self):
        result = self.predictor.predict("AI", [1, 2, 3, 4, 5])
        d = result.to_dict()
        assert "predicted_direction" in d


# ── TrendManager (Integration) ────────────────────────────────────

class TestTrendManager:
    def setup_method(self):
        self.manager = TrendManager()

    def test_analyze_topic_full(self):
        result = self.manager.analyze_topic("AI Jobs", {
            "scores": [{"source": "google_trends", "score": 85, "volume": 5000}],
            "momentum_data": [0.1, 0.3, 0.5, 0.7, 0.8],
            "platform_data": {"twitter": 0.8, "reddit": 0.7, "google_trends": 0.9},
            "virality_data": {"velocity": 60, "engagement_rate": 0.5},
        })
        assert result.topic == "AI Jobs"
        assert result.normalized is not None
        assert result.momentum is not None
        assert result.lifecycle is not None
        assert result.cross_platform is not None
        assert result.confidence is not None
        assert result.explanation is not None
        assert result.recommendation != ""

    def test_analyze_topic_minimal(self):
        result = self.manager.analyze_topic("Crypto", {})
        assert result.topic == "Crypto"

    def test_analyze_batch(self):
        topics = [
            {"topic": "AI", "scores": [{"source": "twitter", "score": 80}]},
            {"topic": "Crypto", "scores": [{"source": "reddit", "score": 70}]},
        ]
        results = self.manager.analyze_batch(topics)
        assert len(results) == 2

    def test_rank_topics(self):
        r1 = self.manager.analyze_topic("AI", {
            "scores": [{"source": "twitter", "score": 90}],
            "platform_data": {"twitter": 0.9, "reddit": 0.8},
        })
        r2 = self.manager.analyze_topic("Crypto", {
            "scores": [{"source": "twitter", "score": 40}],
        })
        ranked = self.manager.rank_topics([r2, r1])
        assert ranked[0].topic == "AI"

    def test_health(self):
        health = self.manager.get_health()
        assert health["status"] == "healthy"
        assert len(health["modules"]) >= 9

    def test_to_dict(self):
        result = self.manager.analyze_topic("AI", {
            "momentum_data": [1, 2, 3, 4, 5],
        })
        d = result.to_dict()
        assert "topic" in d
        assert "confidence" in d


# ── TrendEvidence ──────────────────────────────────────────────────

class TestTrendEvidence:
    def setup_method(self):
        self.builder = TrendEvidenceBuilder()

    def test_build_evidence_full(self):
        evidence = self.builder.build("AI", {
            "momentum": {"velocity": 0.8},
            "lifecycle": {"stage": "growing"},
            "cross_platform": {"platform_count": 4, "consensus_level": 0.8},
            "virality": {"viral_probability": 0.8},
            "confidence": {"overall_confidence": 0.85},
            "seasonality": {"strength": 0.6, "period_days": 7, "pattern_type": "weekly"},
            "competition": {"level": "low"},
        })
        assert len(evidence.evidence_items) > 0
        assert len(evidence.reasoning_steps) > 0
        assert evidence.overall_strength > 0

    def test_build_evidence_empty(self):
        evidence = self.builder.build("AI", {})
        assert len(evidence.evidence_items) == 0

    def test_add_counter_evidence(self):
        evidence = TrendEvidence("AI")
        evidence.add_evidence("source1", "claim1", 0.8)
        evidence.add_counter_evidence("source2", "counter1", 0.5)
        evidence.calculate_strength()
        assert evidence.overall_strength > 0

    def test_evidence_to_dict(self):
        evidence = self.builder.build("AI", {"momentum": {"velocity": 0.8}})
        d = evidence.to_dict()
        assert "evidence" in d
        assert "reasoning" in d
        assert "overall_strength" in d


# ── TrendHistory ───────────────────────────────────────────────────

class TestTrendHistory:
    def setup_method(self):
        self.history = TrendHistory()

    def test_record_snapshot(self):
        snap = self.history.record("AI", score=0.8, momentum=0.5)
        assert snap.topic == "AI"
        assert snap.score == 0.8

    def test_record_multiple(self):
        self.history.record("AI", score=0.5)
        self.history.record("AI", score=0.7)
        self.history.record("AI", score=0.9)
        h = self.history.get_topic_history("AI")
        assert h is not None
        assert len(h.snapshots) == 3
        assert h.peak_score == 0.9

    def test_score_history(self):
        self.history.record("AI", score=0.3)
        self.history.record("AI", score=0.7)
        scores = self.history.get_score_history("AI")
        assert scores == [0.3, 0.7]

    def test_get_trending_topics(self):
        self.history.record("AI", score=0.8)
        self.history.record("Crypto", score=0.3)
        trending = self.history.get_trending_topics(min_score=0.5)
        assert "AI" in trending
        assert "Crypto" not in trending

    def test_max_snapshots_trimmed(self):
        h = TrendHistory(max_snapshots_per_topic=3)
        for i in range(10):
            h.record("AI", score=float(i))
        topic_h = h.get_topic_history("AI")
        assert len(topic_h.snapshots) <= 3

    def test_to_dict(self):
        self.history.record("AI", score=0.8)
        d = self.history.to_dict()
        assert "stats" in d
        assert d["stats"]["total_topics"] == 1

    def test_record_analysis(self):
        from layers.layer03_intelligence.modules.trend_intelligence.trend_manager import TrendAnalysisResult
        result = TrendAnalysisResult("AI")
        snap = self.history.record_analysis("AI", result)
        assert snap.topic == "AI"


# ── TrendEvents ────────────────────────────────────────────────────

class TestTrendEvents:
    def setup_method(self):
        self.bus = TrendEventBus()
        self.emitter = TrendEventEmitter(self.bus)

    def test_publish_event(self):
        event = TrendEvent("trend.detected", "AI", {"score": 0.8})
        self.bus.publish(event)
        assert self.bus.get_event_count() == 1

    def test_subscribe_handler(self):
        received = []
        self.bus.subscribe("trend.detected", lambda e: received.append(e))
        self.bus.publish(TrendEvent("trend.detected", "AI"))
        assert len(received) == 1

    def test_unsubscribe(self):
        received = []
        handler = lambda e: received.append(e)
        self.bus.subscribe("trend.detected", handler)
        self.bus.unsubscribe("trend.detected", handler)
        self.bus.publish(TrendEvent("trend.detected", "AI"))
        assert len(received) == 0

    def test_recent_events(self):
        for i in range(5):
            self.bus.publish(TrendEvent("trend.detected", f"topic_{i}"))
        recent = self.bus.get_recent_events(3)
        assert len(recent) == 3

    def test_events_for_topic(self):
        self.bus.publish(TrendEvent("trend.detected", "AI"))
        self.bus.publish(TrendEvent("trend.detected", "Crypto"))
        self.bus.publish(TrendEvent("trend.updated", "AI"))
        ai_events = self.bus.get_events_for_topic("AI")
        assert len(ai_events) == 2

    def test_emitter_new_trend(self):
        from layers.layer03_intelligence.modules.trend_intelligence.trend_manager import TrendAnalysisResult
        result = TrendAnalysisResult("AI")
        self.emitter.analyze_and_emit("AI", result)
        events = self.bus.get_events_for_topic("AI")
        assert any(e.event_type == "trend.detected" for e in events)

    def test_emitter_lifecycle_change(self):
        from layers.layer03_intelligence.modules.trend_intelligence.trend_manager import TrendAnalysisResult
        from layers.layer03_intelligence.modules.trend_intelligence.lifecycle_detector import LifecycleResult
        r1 = TrendAnalysisResult("AI")
        r1.lifecycle = LifecycleResult("emerging")
        self.emitter.analyze_and_emit("AI", r1)

        r2 = TrendAnalysisResult("AI")
        r2.lifecycle = LifecycleResult("growing")
        self.emitter.analyze_and_emit("AI", r2)

        events = self.bus.get_events_for_topic("AI")
        assert any(e.event_type == "trend.lifecycle.changed" for e in events)

    def test_emitter_virality_spike(self):
        from layers.layer03_intelligence.modules.trend_intelligence.trend_manager import TrendAnalysisResult
        from layers.layer03_intelligence.modules.trend_intelligence.virality_predictor import ViralityResult
        r1 = TrendAnalysisResult("AI")
        v1 = ViralityResult()
        v1.virality_score = 0.3
        r1.virality = v1
        self.emitter.analyze_and_emit("AI", r1)

        r2 = TrendAnalysisResult("AI")
        v2 = ViralityResult()
        v2.virality_score = 0.8
        r2.virality = v2
        self.emitter.analyze_and_emit("AI", r2)

        events = self.bus.get_events_for_topic("AI")
        assert any(e.event_type == "trend.virality.spike" for e in events)

    def test_batch_publish(self):
        events = [TrendEvent("trend.detected", f"t{i}") for i in range(3)]
        self.bus.publish_batch(events)
        assert self.bus.get_event_count() == 3

    def test_clear(self):
        self.bus.publish(TrendEvent("trend.detected", "AI"))
        self.bus.clear()
        assert self.bus.get_event_count() == 0


# ── Integration: Evidence + History + Events in TrendManager ───────

class TestTrendManagerIntegration:
    def setup_method(self):
        self.manager = TrendManager()

    def test_analyze_includes_evidence(self):
        result = self.manager.analyze_topic("AI Jobs", {
            "momentum_data": [0.1, 0.3, 0.5, 0.7],
            "platform_data": {"twitter": 0.8, "reddit": 0.7},
        })
        assert result.evidence is not None
        assert result.evidence.overall_strength >= 0

    def test_analyze_records_history(self):
        self.manager.analyze_topic("AI", {"momentum_data": [1, 2, 3]})
        self.manager.analyze_topic("AI", {"momentum_data": [2, 3, 4]})
        h = self.manager.history.get_topic_history("AI")
        assert h is not None
        assert len(h.snapshots) == 2

    def test_analyze_emits_events(self):
        self.manager.analyze_topic("AI", {"momentum_data": [1, 2, 3]})
        events = self.manager.event_bus.get_events_for_topic("AI")
        assert len(events) > 0

    def test_health_includes_new_modules(self):
        health = self.manager.get_health()
        assert "TrendEvidenceBuilder" in health["modules"]
        assert "TrendHistory" in health["modules"]
        assert "TrendEventEmitter" in health["modules"]

    def test_rank_uses_evidence(self):
        r1 = self.manager.analyze_topic("AI", {
            "scores": [{"source": "twitter", "score": 90}],
            "platform_data": {"twitter": 0.9, "reddit": 0.8},
            "momentum_data": [0.5, 0.7, 0.9],
        })
        r2 = self.manager.analyze_topic("Crypto", {
            "scores": [{"source": "twitter", "score": 40}],
        })
        ranked = self.manager.rank_topics([r2, r1])
        assert ranked[0].topic == "AI"
