"""Tests for shared data models."""

from layers.shared.models.topic import Topic, TopicScore
from layers.shared.models.confidence import ConfidenceResult
from layers.shared.models.evidence import Evidence, EvidenceBundle
from layers.shared.models.decision import DecisionRecord, DecisionTrace
from layers.shared.models.content import ContentPost, ContentVariant
from layers.shared.models.analytics import EngagementMetrics, AnalyticsSnapshot
from layers.shared.models.event import Event, EventType


class TestTopic:
    def test_create(self):
        t = Topic("AI Jobs", niche="technology")
        assert t.title == "AI Jobs"
        assert t.niche == "technology"

    def test_to_dict_roundtrip(self):
        t = Topic("AI", niche="tech", keywords=["ai", "ml"])
        d = t.to_dict()
        t2 = Topic.from_dict(d)
        assert t2.title == "AI"
        assert t2.keywords == ["ai", "ml"]

    def test_repr(self):
        assert "AI" in repr(Topic("AI"))


class TestTopicScore:
    def test_create(self):
        t = Topic("AI")
        ts = TopicScore(t, overall_score=85.0)
        assert ts.overall_score == 85.0

    def test_should_publish(self):
        t = Topic("AI")
        ts = TopicScore(t)
        ts.recommendation = "publish"
        assert ts.should_publish() is True

    def test_should_not_publish(self):
        t = Topic("AI")
        ts = TopicScore(t)
        ts.recommendation = "skip"
        assert ts.should_publish() is False

    def test_score_clamped(self):
        t = Topic("AI")
        ts = TopicScore(t, overall_score=150.0)
        assert ts.overall_score == 100.0

    def test_to_dict_roundtrip(self):
        t = Topic("AI")
        ts = TopicScore(t, overall_score=75.0)
        d = ts.to_dict()
        assert d["overall_score"] == 75.0


class TestConfidenceResult:
    def test_create(self):
        c = ConfidenceResult(confidence=0.85, risk_level="LOW")
        assert c.confidence == 0.85
        assert c.risk_level == "LOW"

    def test_clamped(self):
        c = ConfidenceResult(confidence=1.5)
        assert c.confidence == 1.0
        c2 = ConfidenceResult(confidence=-0.5)
        assert c2.confidence == 0.0

    def test_is_trustworthy(self):
        c = ConfidenceResult(confidence=0.8, risk_level="LOW")
        assert c.is_trustworthy() is True

    def test_not_trustworthy(self):
        c = ConfidenceResult(confidence=0.5, risk_level="HIGH")
        assert c.is_trustworthy() is False

    def test_to_dict_roundtrip(self):
        c = ConfidenceResult(confidence=0.9, reasons=["trend"], evidence=["src1"])
        d = c.to_dict()
        c2 = ConfidenceResult.from_dict(d)
        assert c2.confidence == 0.9
        assert c2.reasons == ["trend"]

    def test_invalid_risk_fallback(self):
        c = ConfidenceResult(risk_level="INVALID")
        assert c.risk_level == "MEDIUM"


class TestEvidence:
    def test_create(self):
        e = Evidence("AI jobs increasing", source="Reuters", credibility=0.9)
        assert e.claim == "AI jobs increasing"
        assert e.credibility == 0.9

    def test_quality_score(self):
        e = Evidence("test", credibility=0.8, freshness=0.6)
        expected = round(0.8 * 0.6 + 0.6 * 0.4, 3)
        assert e.quality_score() == expected

    def test_to_dict_roundtrip(self):
        e = Evidence("claim", source="src", verified=True)
        d = e.to_dict()
        e2 = Evidence.from_dict(d)
        assert e2.claim == "claim"
        assert e2.verified is True


class TestEvidenceBundle:
    def test_add_and_count(self):
        b = EvidenceBundle("AI")
        b.add(Evidence("c1", credibility=0.9))
        b.add(Evidence("c2", credibility=0.7))
        assert b.count() == 2

    def test_overall_credibility(self):
        b = EvidenceBundle("AI")
        b.add(Evidence("c1", credibility=0.8))
        b.add(Evidence("c2", credibility=0.6))
        assert b.overall_credibility == 0.7

    def test_remove(self):
        b = EvidenceBundle("AI")
        e = Evidence("c1")
        b.add(e)
        assert b.remove(e.evidence_id) is True
        assert b.count() == 0

    def test_get_verified(self):
        b = EvidenceBundle("AI")
        b.add(Evidence("c1", verified=True))
        b.add(Evidence("c2", verified=False))
        assert len(b.get_verified()) == 1


class TestDecisionRecord:
    def test_create(self):
        d = DecisionRecord("Why AI?", "High demand", confidence=0.9)
        assert d.question == "Why AI?"
        assert d.confidence == 0.9

    def test_to_dict_roundtrip(self):
        d = DecisionRecord("Q", "A", confidence=0.8, module="trend")
        dr = d.to_dict()
        d2 = DecisionRecord.from_dict(dr)
        assert d2.question == "Q"
        assert d2.module == "trend"


class TestDecisionTrace:
    def test_add_and_count(self):
        trace = DecisionTrace("AI")
        trace.add(DecisionRecord("Q1", "A1", confidence=0.9))
        trace.add(DecisionRecord("Q2", "A2", confidence=0.7))
        assert trace.count() == 2
        assert trace.overall_confidence == 0.8

    def test_get_by_module(self):
        trace = DecisionTrace("AI")
        trace.add(DecisionRecord("Q1", module="trend"))
        trace.add(DecisionRecord("Q2", module="verify"))
        assert len(trace.get_by_module("trend")) == 1

    def test_get_lowest_confidence(self):
        trace = DecisionTrace("AI")
        trace.add(DecisionRecord("Q1", confidence=0.9))
        trace.add(DecisionRecord("Q2", confidence=0.3))
        lowest = trace.get_lowest_confidence()
        assert lowest.confidence == 0.3

    def test_empty_trace(self):
        trace = DecisionTrace("AI")
        assert trace.get_lowest_confidence() is None
        assert trace.count() == 0


class TestContentPost:
    def test_create(self):
        p = ContentPost(title="AI Jobs", body="Great opportunities", topic="AI")
        assert p.title == "AI Jobs"
        assert p.status == "draft"

    def test_word_count(self):
        p = ContentPost(body="one two three four five")
        assert p.word_count() == 5

    def test_to_dict_roundtrip(self):
        p = ContentPost(title="T", body="B", hashtags=["ai"])
        d = p.to_dict()
        p2 = ContentPost.from_dict(d)
        assert p2.title == "T"
        assert p2.hashtags == ["ai"]


class TestContentVariant:
    def test_create(self):
        p = ContentPost(title="Test")
        v = ContentVariant(p, "A")
        assert v.variant_label == "A"


class TestEngagementMetrics:
    def test_create(self):
        m = EngagementMetrics()
        assert m.likes == 0

    def test_total_engagement(self):
        m = EngagementMetrics()
        m.likes = 10
        m.comments = 5
        m.shares = 3
        assert m.total_engagement() == 18

    def test_engagement_rate(self):
        m = EngagementMetrics()
        m.likes = 10
        m.reach = 100
        rate = m.calculate_engagement_rate()
        assert rate == 0.1

    def test_engagement_rate_zero_reach(self):
        m = EngagementMetrics()
        assert m.calculate_engagement_rate() == 0.0


class TestAnalyticsSnapshot:
    def test_create(self):
        s = AnalyticsSnapshot(post_id="p1", topic="AI")
        assert s.post_id == "p1"

    def test_to_dict_roundtrip(self):
        s = AnalyticsSnapshot(post_id="p1", topic="AI")
        d = s.to_dict()
        s2 = AnalyticsSnapshot.from_dict(d)
        assert s2.post_id == "p1"


class TestEvent:
    def test_create(self):
        e = Event(EventType.POST_PUBLISHED, source="layer07", data={"post_id": "123"})
        assert e.event_type == EventType.POST_PUBLISHED
        assert e.source == "layer07"

    def test_to_dict_roundtrip(self):
        e = Event(EventType.TOPIC_DISCOVERED, data={"topic": "AI"})
        d = e.to_dict()
        e2 = Event.from_dict(d)
        assert e2.event_type == EventType.TOPIC_DISCOVERED
        assert e2.data["topic"] == "AI"

    def test_event_type_as_string(self):
        e = Event("post.published", source="test")
        assert e.event_type == "post.published"

    def test_repr(self):
        e = Event(EventType.AGENT_STARTED, source="main")
        assert "EventType.AGENT_STARTED" in repr(e)
