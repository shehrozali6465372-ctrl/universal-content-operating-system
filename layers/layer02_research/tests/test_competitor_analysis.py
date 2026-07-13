"""
Tests for Competitor Analysis Module
Layer 2: Research Engine — Module 3

Run: python -m pytest layers/layer02_research/tests/test_competitor_analysis.py -v
"""

import pytest

from layers.layer02_research.modules.competitor_analysis.competitor_profile import CompetitorProfile
from layers.layer02_research.modules.competitor_analysis.content_analyzer import ContentAnalyzer, ContentPost
from layers.layer02_research.modules.competitor_analysis.posting_pattern_analyzer import PostingPatternAnalyzer, PostingPattern
from layers.layer02_research.modules.competitor_analysis.engagement_analyzer import EngagementAnalyzer, EngagementMetrics
from layers.layer02_research.modules.competitor_analysis.writing_style_analyzer import WritingStyleAnalyzer, WritingStyleProfile
from layers.layer02_research.modules.competitor_analysis.gap_detector import GapDetector, ContentGap
from layers.layer02_research.modules.competitor_analysis.opportunity_finder import OpportunityFinder, Opportunity
from layers.layer02_research.modules.competitor_analysis.competitor_intel_manager import CompetitorIntelManager
from layers.layer02_research.modules.competitor_analysis.exceptions import (
    CompetitorNotFoundError, DuplicateCompetitorError,
)


# ═══════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════

@pytest.fixture
def manager(tmp_path):
    return CompetitorIntelManager(storage_path=str(tmp_path / "competitors.json"))


def _make_posts(count=10, base_engagement=50):
    """Helper to create sample ContentPost list."""
    posts = []
    topics = ["finance", "tech", "health", "marketing", "ai"]
    formats = ["text", "carousel", "video", "image"]
    for i in range(count):
        posts.append(ContentPost(
            post_id=f"post_{i}",
            content_type=formats[i % len(formats)],
            topic=topics[i % len(topics)],
            text=f"This is post {i} about {topics[i % len(topics)]}. " * 5,
            hashtags=[f"#{topics[i % len(topics)]}", "#test"],
            likes=base_engagement + i * 10,
            comments=5 + i * 2,
            shares=2 + i,
            posted_at=f"2026-07-{(i % 28) + 1:02d}T{(10 + i) % 24}:00:00+00:00",
            has_image=i % 3 == 0,
            has_video=i % 4 == 0,
            sentiment="positive" if i % 3 == 0 else "neutral",
        ))
    return posts


@pytest.fixture
def manager_with_competitors(manager):
    """Manager with pre-populated competitors and posts."""
    competitors = [
        ("Finance Hub", "ai", "finance", 50000, 9.0, 6.0, 3.0),
        ("Tech Weekly", "technology", "tech", 120000, 7.5, 7.0, 5.0),
        ("Health First", "health", "health", 30000, 8.0, 5.0, 4.0),
        ("Marketing Pro", "marketing", "business", 80000, 6.0, 6.5, 6.0),
        ("AI Insider", "ai", "ai", 200000, 8.5, 8.0, 4.0),
    ]
    for name, niche, cat, followers, eng, aud, comp in competitors:
        profile = manager.add_competitor(
            page_name=name, niche=niche, category=cat, followers=followers,
            avg_engagement_rate=eng, avg_likes=eng * 10, avg_comments=eng * 2, avg_shares=eng,
            top_topics=[niche, cat], top_formats=["text", "video"], confidence=0.8,
        )
        # Add posts for each competitor
        manager.add_posts(profile.competitor_id, _make_posts(15, base_engagement=int(eng * 5)))

    return manager


# ═══════════════════════════════════════════
# Test 1: Competitor Profile
# ═══════════════════════════════════════════

class TestCompetitorProfile:
    def test_create_profile(self):
        p = CompetitorProfile("Test Page", followers=1000)
        assert p.page_name == "Test Page"
        assert p.followers == 1000
        assert p.status == "active"

    def test_follower_tier(self):
        assert CompetitorProfile("A", followers=500).get_follower_tier() == "micro"
        assert CompetitorProfile("B", followers=5000).get_follower_tier() == "small"
        assert CompetitorProfile("C", followers=50000).get_follower_tier() == "medium"
        assert CompetitorProfile("D", followers=500000).get_follower_tier() == "large"
        assert CompetitorProfile("E", followers=5000000).get_follower_tier() == "mega"

    def test_opportunity_score(self):
        p = CompetitorProfile("Opp", growth_score=8.0)
        p.content_gaps = ["gap1", "gap2", "gap3"]
        p.weaknesses = ["weak1", "weak2"]
        score = p.calculate_opportunity_score()
        assert score > 0

    def test_engagement_total(self):
        p = CompetitorProfile("Eng", avg_likes=100, avg_comments=20, avg_shares=10)
        assert p.get_engagement_total() == 130

    def test_is_analyzable(self):
        p = CompetitorProfile("Good", followers=1000, post_count=50, confidence=0.5)
        assert p.is_analyzable() is True
        p2 = CompetitorProfile("Bad", followers=0)
        assert p2.is_analyzable() is False

    def test_to_dict(self):
        p = CompetitorProfile("Dict", niche="ai", followers=100)
        d = p.to_dict()
        assert d["page_name"] == "Dict"
        assert d["niche"] == "ai"
        assert "competitor_id" in d

    def test_from_dict(self):
        d = {
            "page_name": "Restore", "niche": "finance",
            "followers": 5000, "avg_engagement_rate": 7.5,
        }
        p = CompetitorProfile.from_dict(d)
        assert p.page_name == "Restore"
        assert p.followers == 5000

    def test_from_dict_preserves_id(self):
        d = {"page_name": "X", "competitor_id": "custom_id"}
        p = CompetitorProfile.from_dict(d)
        assert p.competitor_id == "custom_id"

    def test_niche_invalid(self):
        p = CompetitorProfile("X", niche="invalid")
        assert p.niche == "general"

    def test_engagement_rate_clamped(self):
        p = CompetitorProfile("X", avg_engagement_rate=150)
        assert p.avg_engagement_rate == 100.0

    def test_negative_followers(self):
        p = CompetitorProfile("X", followers=-100)
        assert p.followers == 0

    def test_growth_score_clamped(self):
        p = CompetitorProfile("X", growth_score=15.0)
        assert p.growth_score == 10.0


# ═══════════════════════════════════════════
# Test 2: Content Analyzer
# ═══════════════════════════════════════════

class TestContentAnalyzer:
    def test_add_and_get_posts(self):
        ca = ContentAnalyzer()
        posts = _make_posts(5)
        ca.add_posts("comp1", posts)
        assert len(ca.get_posts("comp1")) == 5

    def test_analyze_topics(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(10))
        topics = ca.analyze_topics("comp1")
        assert len(topics) > 0
        assert sum(topics.values()) == 10

    def test_analyze_formats(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(8))
        fmts = ca.analyze_formats("comp1")
        assert len(fmts) > 0

    def test_analyze_hashtags(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(5))
        tags = ca.analyze_hashtags("comp1", top_n=5)
        assert len(tags) > 0
        assert tags[0][0].startswith("#")

    def test_analyze_media_usage(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(6))
        media = ca.analyze_media_usage("comp1")
        assert "image_pct" in media
        assert 0 <= media["image_pct"] <= 100

    def test_analyze_media_usage_empty(self):
        ca = ContentAnalyzer()
        media = ca.analyze_media_usage("empty")
        assert media["text_only_pct"] == 0

    def test_analyze_sentiment(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(9))
        sent = ca.analyze_sentiment("comp1")
        assert "positive" in sent or "neutral" in sent

    def test_get_top_posts(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(10))
        top = ca.get_top_posts("comp1", count=3)
        assert len(top) == 3
        assert top[0].total_engagement >= top[-1].total_engagement

    def test_get_average_word_count(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(5))
        avg = ca.get_average_word_count("comp1")
        assert avg > 0

    def test_detect_content_themes(self):
        ca = ContentAnalyzer()
        ca.add_posts("comp1", _make_posts(10))
        themes = ca.detect_content_themes("comp1")
        assert len(themes) > 0
        for theme, data in themes.items():
            assert "post_count" in data
            assert "avg_engagement" in data

    def test_content_post_engagement(self):
        p = ContentPost(likes=10, comments=5, shares=3)
        assert p.total_engagement == 18

    def test_content_post_word_count(self):
        p = ContentPost(text="hello world foo bar")
        assert p.word_count == 4


# ═══════════════════════════════════════════
# Test 3: Posting Pattern Analyzer
# ═══════════════════════════════════════════

class TestPostingPatternAnalyzer:
    def test_analyze_empty(self):
        ppa = PostingPatternAnalyzer()
        pattern = ppa.analyze("comp1", [])
        assert pattern.posting_frequency == "unknown"

    def test_analyze_with_posts(self):
        ppa = PostingPatternAnalyzer()
        posts = _make_posts(20)
        pattern = ppa.analyze("comp1", posts)
        assert pattern.avg_posts_per_day >= 0
        assert len(pattern.best_hours) > 0

    def test_frequency_labels(self):
        ppa = PostingPatternAnalyzer()
        # Create posts all on same day (high frequency)
        posts = [ContentPost(posted_at=f"2026-07-01T{h:02d}:00:00+00:00") for h in range(12)]
        pattern = ppa.analyze("comp1", posts)
        assert pattern.posting_frequency in ("very_high", "high")

    def test_dead_zones(self):
        ppa = PostingPatternAnalyzer()
        posts = [ContentPost(posted_at=f"2026-07-01T{h:02d}:00:00+00:00") for h in [9, 10, 11, 12]]
        pattern = ppa.analyze("comp1", posts)
        assert len(pattern.dead_zones) > 0

    def test_consistency_score(self):
        ppa = PostingPatternAnalyzer()
        posts = [ContentPost(posted_at=f"2026-07-{d:02d}T10:00:00+00:00") for d in range(1, 8)]
        pattern = ppa.analyze("comp1", posts)
        assert pattern.consistency_score > 0

    def test_find_gap_windows(self):
        ppa = PostingPatternAnalyzer()
        posts = [ContentPost(posted_at=f"2026-07-01T{h:02d}:00:00+00:00") for h in [9, 10, 17, 18]]
        ppa.analyze("comp1", posts)
        gaps = ppa.find_gap_windows("comp1", min_gap_hours=4)
        assert len(gaps) > 0

    def test_compare_patterns(self):
        ppa = PostingPatternAnalyzer()
        posts = _make_posts(10)
        ppa.analyze("comp_a", posts)
        ppa.analyze("comp_b", posts)
        cmp = ppa.compare_patterns("comp_a", "comp_b")
        assert "frequency_diff" in cmp

    def test_compare_patterns_missing(self):
        ppa = PostingPatternAnalyzer()
        cmp = ppa.compare_patterns("x", "y")
        assert "error" in cmp

    def test_get_exploitable_hours(self):
        ppa = PostingPatternAnalyzer()
        posts = [ContentPost(posted_at=f"2026-07-01T{h:02d}:00:00+00:00") for h in [9, 10, 11]]
        ppa.analyze("comp1", posts)
        hours = ppa.get_exploitable_hours("comp1")
        assert 9 not in hours
        assert len(hours) > 15

    def test_pattern_to_dict(self):
        p = PostingPattern("x")
        d = p.to_dict()
        assert d["competitor_id"] == "x"


# ═══════════════════════════════════════════
# Test 4: Engagement Analyzer
# ═══════════════════════════════════════════

class TestEngagementAnalyzer:
    def test_analyze_empty(self):
        ea = EngagementAnalyzer()
        m = ea.analyze("comp1", [])
        assert m.total_posts == 0

    def test_analyze_with_posts(self):
        ea = EngagementAnalyzer()
        posts = _make_posts(15, base_engagement=100)
        m = ea.analyze("comp1", posts)
        assert m.total_posts == 15
        assert m.total_engagement > 0
        assert m.avg_likes > 0

    def test_engagement_rate(self):
        ea = EngagementAnalyzer()
        posts = [ContentPost(likes=100, comments=10, shares=5)]
        m = ea.analyze("comp1", posts)
        assert m.avg_engagement_rate > 0

    def test_viral_posts_detected(self):
        ea = EngagementAnalyzer()
        # Create posts where one is much higher
        posts = [ContentPost(post_id=f"p{i}", likes=10) for i in range(10)]
        posts.append(ContentPost(post_id="viral", likes=1000))
        m = ea.analyze("comp1", posts)
        assert "viral" in m.viral_posts

    def test_engagement_trend(self):
        ea = EngagementAnalyzer()
        # First half low, second half high → growing
        posts = [ContentPost(likes=10, comments=1, shares=0) for _ in range(5)]
        posts += [ContentPost(likes=100, comments=20, shares=10) for _ in range(5)]
        m = ea.analyze("comp1", posts)
        assert m.engagement_trend == "growing"

    def test_engagement_trend_declining(self):
        ea = EngagementAnalyzer()
        posts = [ContentPost(likes=100, comments=20, shares=10) for _ in range(5)]
        posts += [ContentPost(likes=10, comments=1, shares=0) for _ in range(5)]
        m = ea.analyze("comp1", posts)
        assert m.engagement_trend == "declining"

    def test_volatility(self):
        ea = EngagementAnalyzer()
        posts = [ContentPost(likes=100) for _ in range(10)]
        m = ea.analyze("comp1", posts)
        assert m.engagement_volatility == 0.0  # All same = no volatility

    def test_find_viral_patterns(self):
        ea = EngagementAnalyzer()
        posts = _make_posts(10, base_engagement=100)
        ea.analyze("comp1", posts)
        viral = ea.find_viral_patterns("comp1", posts)
        assert "viral_count" in viral

    def test_compare_engagement(self):
        ea = EngagementAnalyzer()
        posts_a = [ContentPost(likes=100, comments=20, shares=10) for _ in range(5)]
        posts_b = [ContentPost(likes=100, comments=2, shares=1) for _ in range(5)]
        ea.analyze("a", posts_a)
        ea.analyze("b", posts_b)
        cmp = ea.compare_engagement("a", "b")
        assert cmp["winner"] == "A"

    def test_get_weaknesses(self):
        ea = EngagementAnalyzer()
        posts = [ContentPost(likes=0, comments=0, shares=0)]
        ea.analyze("comp1", posts)
        weaknesses = ea.get_weaknesses("comp1")
        assert len(weaknesses) > 0

    def test_get_strengths(self):
        ea = EngagementAnalyzer()
        posts = [ContentPost(likes=200, comments=50, shares=30) for _ in range(5)]
        ea.analyze("comp1", posts)
        strengths = ea.get_strengths("comp1")
        assert len(strengths) > 0

    def test_metrics_to_dict(self):
        m = EngagementMetrics("x")
        d = m.to_dict()
        assert d["competitor_id"] == "x"


# ═══════════════════════════════════════════
# Test 5: Writing Style Analyzer
# ═══════════════════════════════════════════

class TestWritingStyleAnalyzer:
    def test_analyze_empty(self):
        wsa = WritingStyleAnalyzer()
        p = wsa.analyze("comp1", [])
        assert p.avg_word_count == 0

    def test_analyze_with_texts(self):
        wsa = WritingStyleAnalyzer()
        texts = [
            "This is a great post about AI! 😊",
            "Learn how to use Python for data science.",
            "Check out our new course on machine learning!",
        ]
        p = wsa.analyze("comp1", texts)
        assert p.avg_word_count > 0
        assert p.tone != "unknown"

    def test_tone_detection(self):
        wsa = WritingStyleAnalyzer()
        texts = ["LOL this is so funny 😂 hahaha", "What a joke! 😂"] * 5
        p = wsa.analyze("comp1", texts)
        assert p.tone in ("humorous", "neutral")

    def test_educational_tone(self):
        wsa = WritingStyleAnalyzer()
        texts = ["Learn how to code", "Tutorial: step by step guide", "How to learn Python"] * 5
        p = wsa.analyze("comp1", texts)
        assert p.tone == "educational"

    def test_emoji_frequency(self):
        wsa = WritingStyleAnalyzer()
        texts = ["Hello 😊 🎉 🔥", "World 😂"]
        p = wsa.analyze("comp1", texts)
        assert p.emoji_frequency > 0

    def test_question_frequency(self):
        wsa = WritingStyleAnalyzer()
        texts = ["What do you think?", "How about this?", "Ready?"]
        p = wsa.analyze("comp1", texts)
        assert p.question_frequency > 0

    def test_post_length_category(self):
        wsa = WritingStyleAnalyzer()
        short = ["Hi there"]
        p = wsa.analyze("comp1", short)
        assert p.post_length_category == "short"

    def test_readability_score(self):
        wsa = WritingStyleAnalyzer()
        texts = ["This is a simple sentence. It is easy to read. Short words help."]
        p = wsa.analyze("comp1", texts)
        assert 0 <= p.readability_score <= 100

    def test_cta_patterns(self):
        wsa = WritingStyleAnalyzer()
        texts = ["Click here to learn more! Sign up now for our free guide."]
        p = wsa.analyze("comp1", texts)
        assert "click here" in p.cta_patterns

    def test_voice_detection(self):
        wsa = WritingStyleAnalyzer()
        texts = ["I think this is great. We should do more. Our team is amazing."] * 5
        p = wsa.analyze("comp1", texts)
        assert p.voice == "first_person"

    def test_voice_second_person(self):
        wsa = WritingStyleAnalyzer()
        texts = ["You can do this. Your journey starts here. Are you ready?"] * 5
        p = wsa.analyze("comp1", texts)
        assert p.voice == "second_person"

    def test_detect_differentiation(self):
        wsa = WritingStyleAnalyzer()
        our = WritingStyleProfile("ours")
        our.tone = "casual"
        our.post_length_category = "short"
        our.emoji_frequency = 0.5
        our.cta_patterns = ["sign up"]
        their = WritingStyleProfile("theirs")
        their.tone = "professional"
        their.post_length_category = "long"
        their.emoji_frequency = 3.0
        their.cta_patterns = []
        diffs = wsa.detect_differentiation(our, their)
        assert len(diffs) > 0

    def test_profile_to_dict(self):
        p = WritingStyleProfile("x")
        d = p.to_dict()
        assert d["competitor_id"] == "x"


# ═══════════════════════════════════════════
# Test 6: Gap Detector
# ═══════════════════════════════════════════

class TestGapDetector:
    def test_detect_topic_gaps(self):
        gd = GapDetector()
        comps = [
            CompetitorProfile("A", niche="ai", top_topics=["python", "ml"]),
            CompetitorProfile("B", niche="ai", top_topics=["python", "dl"]),
        ]
        gaps = gd.detect_topic_gaps(comps, ["python", "ml", "dl", "robotics"])
        topic_gaps = [g for g in gaps if g.gap_type == "topic"]
        assert any("robotics" in g.description for g in topic_gaps)

    def test_detect_format_gaps(self):
        gd = GapDetector()
        comps = [CompetitorProfile("A", top_formats=["text", "video"])]
        gaps = gd.detect_format_gaps(comps)
        assert any(g.gap_type == "format" for g in gaps)

    def test_detect_audience_gaps(self):
        gd = GapDetector()
        comps = [
            CompetitorProfile(f"C{i}", niche="ai") for i in range(5)
        ]
        gaps = gd.detect_audience_gaps(comps)
        assert any("ai" in g.description for g in gaps)

    def test_detect_depth_gaps(self):
        gd = GapDetector()
        comp = CompetitorProfile("Shallow", top_topics=["only_one"], post_count=50)
        gaps = gd.detect_depth_gaps([comp])
        assert any(g.gap_type == "depth" for g in gaps)

    def test_detect_all(self):
        gd = GapDetector()
        comps = [CompetitorProfile("A", top_topics=["x"], top_formats=["text"])]
        all_gaps = gd.detect_all(comps, ["x", "y"])
        assert len(all_gaps) > 0

    def test_gap_to_dict(self):
        g = ContentGap("test", "desc", "high", 8.0, "evidence")
        d = g.to_dict()
        assert d["gap_type"] == "test"
        assert d["severity"] == "high"

    def test_gap_severity_invalid(self):
        g = ContentGap("t", "d", severity="invalid")
        assert g.severity == "medium"

    def test_store_and_get(self):
        gd = GapDetector()
        gaps = [ContentGap("topic", "test gap")]
        gd.store_gaps("comp1", gaps)
        assert len(gd.get_gaps_for_competitor("comp1")) == 1

    def test_get_top_gaps(self):
        gd = GapDetector()
        gd.store_gaps("a", [ContentGap("topic", "low", opportunity_score=3.0)])
        gd.store_gaps("b", [ContentGap("topic", "high", opportunity_score=9.0)])
        top = gd.get_top_gaps(1)
        assert top[0].opportunity_score == 9.0


# ═══════════════════════════════════════════
# Test 7: Opportunity Finder
# ═══════════════════════════════════════════

class TestOpportunityFinder:
    def test_discover_weaknesses(self):
        of = OpportunityFinder()
        comp = CompetitorProfile("Weak", followers=10000)
        comp.weaknesses = ["Low engagement", "No videos"]
        opps = of._weakness_exploitation([comp], None)
        assert len(opps) > 0
        assert opps[0].opp_type == "weakness_exploitation"

    def test_format_innovation(self):
        of = OpportunityFinder()
        comp = CompetitorProfile("A", top_formats=["text", "image"])
        opps = of._content_format_innovation([comp])
        assert any("reel" in o.description for o in opps)

    def test_audience_expansion(self):
        of = OpportunityFinder()
        comp = CompetitorProfile("A", niche="finance")
        opps = of._audience_expansion([comp])
        assert len(opps) > 0

    def test_timing_opportunities(self):
        of = OpportunityFinder()
        comp = CompetitorProfile("A", best_post_times=["09:00", "12:00"])
        opps = of._timing_opportunities([comp])
        assert len(opps) > 0

    def test_gap_to_opportunity(self):
        of = OpportunityFinder()
        gaps = [ContentGap("topic", "No one covers X", "high", 8.0)]
        opps = of._gap_to_opportunity(gaps)
        assert len(opps) == 1
        assert opps[0].impact_score == 8.0

    def test_discover_all(self):
        of = OpportunityFinder()
        comp = CompetitorProfile("A", niche="ai", top_formats=["text"])
        comp.weaknesses = ["weak"]
        opps = of.discover_all([comp])
        assert len(opps) > 0

    def test_opportunity_to_dict(self):
        o = Opportunity("test", "desc", "high", "low", 8.0)
        d = o.to_dict()
        assert d["opp_type"] == "test"
        assert d["priority"] == "high"

    def test_opportunity_invalid_priority(self):
        o = Opportunity("t", "d", priority="invalid")
        assert o.priority == "medium"

    def test_opportunity_invalid_effort(self):
        o = Opportunity("t", "d", effort_level="extreme")
        assert o.effort_level == "medium"

    def test_store_and_get(self):
        of = OpportunityFinder()
        opps = [Opp := Opportunity("test", "desc")]
        of.store_opportunities("comp1", opps)
        assert len(of.get_top_opportunities()) >= 1


# ═══════════════════════════════════════════
# Test 8: Competitor Intel Manager — CRUD
# ═══════════════════════════════════════════

class TestManagerCRUD:
    def test_add_competitor(self, manager):
        c = manager.add_competitor("Test Page", followers=5000)
        assert c.page_name == "Test Page"
        assert manager.exists("Test Page")

    def test_add_duplicate_raises(self, manager):
        manager.add_competitor("Unique")
        with pytest.raises(DuplicateCompetitorError):
            manager.add_competitor("Unique")

    def test_case_insensitive_dup(self, manager):
        manager.add_competitor("CaseTest")
        with pytest.raises(DuplicateCompetitorError):
            manager.add_competitor("casetest")

    def test_get_competitor(self, manager):
        c = manager.add_competitor("GetMe")
        found = manager.get_competitor(c.competitor_id)
        assert found.page_name == "GetMe"

    def test_get_not_found(self, manager):
        with pytest.raises(CompetitorNotFoundError):
            manager.get_competitor("ghost")

    def test_get_by_name(self, manager):
        manager.add_competitor("ByName")
        found = manager.get_by_name("byname")
        assert found is not None

    def test_get_by_name_not_found(self, manager):
        assert manager.get_by_name("ghost") is None

    def test_update_competitor(self, manager):
        c = manager.add_competitor("Update")
        manager.update_competitor(c.competitor_id, followers=99999)
        updated = manager.get_competitor(c.competitor_id)
        assert updated.followers == 99999

    def test_update_not_found(self, manager):
        with pytest.raises(CompetitorNotFoundError):
            manager.update_competitor("nope", followers=1)

    def test_delete_competitor(self, manager):
        c = manager.add_competitor("DeleteMe")
        assert manager.delete_competitor(c.competitor_id) is True
        assert not manager.exists("DeleteMe")

    def test_delete_not_found(self, manager):
        with pytest.raises(CompetitorNotFoundError):
            manager.delete_competitor("ghost")

    def test_list_competitors(self, manager):
        manager.add_competitor("A", niche="ai")
        manager.add_competitor("B", niche="cooking")
        assert len(manager.list_competitors()) == 2

    def test_list_by_niche(self, manager):
        manager.add_competitor("A", niche="ai")
        manager.add_competitor("B", niche="ai")
        manager.add_competitor("C", niche="cooking")
        assert len(manager.list_competitors(niche="ai")) == 2

    def test_list_by_status(self, manager):
        c = manager.add_competitor("Active")
        manager.update_competitor(c.competitor_id, status="archived")
        assert len(manager.list_competitors(status="active")) == 0


# ═══════════════════════════════════════════
# Test 9: Manager — Analysis Pipeline
# ═══════════════════════════════════════════

class TestManagerAnalysis:
    def test_add_posts(self, manager_with_competitors):
        comps = manager_with_competitors.list_competitors()
        assert len(comps) > 0
        posts = manager_with_competitors.content_analyzer.get_posts(comps[0].competitor_id)
        assert len(posts) > 0

    def test_run_full_analysis(self, manager_with_competitors):
        comps = manager_with_competitors.list_competitors()
        result = manager_with_competitors.run_full_analysis(comps[0].competitor_id)
        assert result.data_quality == "analyzed"
        assert result.posting_frequency != "unknown"
        assert len(result.strengths) > 0 or len(result.weaknesses) > 0

    def test_detect_gaps(self, manager_with_competitors):
        gaps = manager_with_competitors.detect_gaps(known_topics=["ai", "python", "robotics"])
        assert isinstance(gaps, list)

    def test_find_opportunities(self, manager_with_competitors):
        manager_with_competitors.detect_gaps()
        opps = manager_with_competitors.find_opportunities()
        assert isinstance(opps, list)

    def test_compare_two(self, manager_with_competitors):
        comps = manager_with_competitors.list_competitors()
        if len(comps) >= 2:
            cmp = manager_with_competitors.compare_two(comps[0].competitor_id, comps[1].competitor_id)
            assert "competitor_a" in cmp
            assert "competitor_b" in cmp

    def test_leaderboard(self, manager_with_competitors):
        lb = manager_with_competitors.get_leaderboard()
        assert len(lb) > 0
        assert lb[0]["rank"] == 1
        assert "name" in lb[0]


# ═══════════════════════════════════════════
# Test 10: Persistence & Health
# ═══════════════════════════════════════════

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "persist.json"
        m1 = CompetitorIntelManager(storage_path=str(path))
        m1.add_competitor("Persist", followers=5000)
        m2 = CompetitorIntelManager(storage_path=str(path))
        assert len(m2.list_competitors()) == 1
        assert m2.list_competitors()[0].page_name == "Persist"

    def test_no_storage(self):
        m = CompetitorIntelManager()
        m.add_competitor("NoStorage")
        assert m.exists("NoStorage")

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid json")
        m = CompetitorIntelManager(storage_path=str(path))
        assert len(m.list_competitors()) == 0

    def test_health_check_empty(self, manager):
        h = manager.health_check()
        assert h["total_competitors"] == 0
        assert h["content_analyzer_ready"] is True

    def test_health_check_with_data(self, manager_with_competitors):
        h = manager_with_competitors.health_check()
        assert h["total_competitors"] == 5
        assert h["active"] == 5


# ═══════════════════════════════════════════
# Test 11: Edge Cases
# ═══════════════════════════════════════════

class TestEdgeCases:
    def test_all_niches(self, manager):
        for niche in CompetitorProfile.NICHES:
            c = manager.add_competitor(f"Test_{niche}", niche=niche)
            assert c.niche == niche

    def test_special_characters(self, manager):
        c = manager.add_competitor("Page @#$%^&*()")
        assert c.page_name == "Page @#$%^&*()"

    def test_many_competitors_performance(self, manager):
        for i in range(50):
            manager.add_competitor(f"Comp_{i}", niche="general", followers=i * 1000)
        assert len(manager.list_competitors()) == 50

    def test_concurrent_access(self, manager):
        import threading
        errors = []

        def add_comp(i):
            try:
                manager.add_competitor(f"Thread_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_comp, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(manager.list_competitors()) == 20

    def test_empty_post_analysis(self, manager):
        c = manager.add_competitor("Empty")
        result = manager.run_full_analysis(c.competitor_id)
        assert result.page_name == "Empty"

    def test_competitor_profile_from_dict_all_fields(self):
        d = {
            "page_name": "Full", "page_url": "https://example.com",
            "niche": "finance", "category": "cat", "followers": 1000,
            "following": 500, "post_count": 100,
            "posting_frequency": "high", "best_post_times": ["09:00"],
            "avg_posts_per_day": 2.0, "top_topics": ["a", "b"],
            "top_hashtags": ["#a"], "top_formats": ["video"],
            "writing_style": "formal", "tone": "professional",
            "image_style": "clean", "brand_colors": ["#fff"],
            "avg_engagement_rate": 5.0, "avg_likes": 100,
            "avg_comments": 20, "avg_shares": 10,
            "engagement_trend": "growing", "growth_score": 7.0,
            "confidence": 0.9, "tags": ["hot"], "metadata": {"k": "v"},
            "competitor_id": "custom_id", "opportunity_score": 8.0,
            "content_gaps": ["gap1"], "weaknesses": ["w1"],
            "strengths": ["s1"], "data_quality": "full",
            "status": "monitoring", "created_at": "2026-01-01",
            "updated_at": "2026-06-01", "last_analyzed": "2026-07-01",
        }
        p = CompetitorProfile.from_dict(d)
        assert p.competitor_id == "custom_id"
        assert p.page_url == "https://example.com"
        assert p.followers == 1000
        assert p.content_gaps == ["gap1"]
        assert p.status == "monitoring"
