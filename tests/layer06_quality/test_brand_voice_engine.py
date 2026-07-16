"""Tests for Layer 6 Module 7 — Brand Voice & Consistency Engine."""
from layers.layer06_quality.modules.brand_voice_engine.brand_profile import BrandProfile, create_default_profile, INDUSTRY_PROFILES
from layers.layer06_quality.modules.brand_voice_engine.tone_checker import ToneChecker
from layers.layer06_quality.modules.brand_voice_engine.vocabulary_checker import VocabularyChecker
from layers.layer06_quality.modules.brand_voice_engine.style_analyzer import StyleAnalyzer
from layers.layer06_quality.modules.brand_voice_engine.brand_voice_engine import BrandVoiceEngine
from layers.layer06_quality.modules.brand_voice_engine.voice_report import VoiceReport, VoiceComponentScore


# ── BrandProfile Tests ──

class TestBrandProfile:
    def test_default_profile(self):
        profile = create_default_profile("TestBrand")
        assert profile.brand_name == "TestBrand"
        assert profile.tone == "professional"

    def test_to_dict(self):
        profile = create_default_profile("Brand")
        d = profile.to_dict()
        assert "brand_name" in d
        assert "tone" in d
        assert "personality" in d

    def test_from_dict(self):
        data = {"brand_name": "MyBrand", "tone": "casual", "formality_level": 0.3}
        profile = BrandProfile.from_dict(data)
        assert profile.brand_name == "MyBrand"
        assert profile.tone == "casual"

    def test_industry_profiles_exist(self):
        assert "tech" in INDUSTRY_PROFILES
        assert "finance" in INDUSTRY_PROFILES
        assert "lifestyle" in INDUSTRY_PROFILES

    def test_forbidden_words(self):
        profile = create_default_profile("Brand")
        profile.forbidden_words = ["cheap", "low quality"]
        assert "cheap" in profile.forbidden_words

    def test_terminology(self):
        profile = create_default_profile("Brand")
        profile.terminology = {"AI": "artificial intelligence", "ML": "machine learning"}
        assert profile.terminology["AI"] == "artificial intelligence"


# ── ToneChecker Tests ──

class TestToneChecker:
    def setup_method(self):
        self.checker = ToneChecker()

    def test_formal_content_matches_formal_profile(self):
        profile = create_default_profile("Brand")
        profile.tone = "formal"
        score = self.checker.check(
            "Furthermore, the analysis demonstrates significant market potential.", profile
        )
        assert isinstance(score, VoiceComponentScore)
        assert score.score >= 0.7

    def test_casual_content_mismatches_formal_profile(self):
        profile = create_default_profile("Brand")
        profile.tone = "formal"
        score = self.checker.check(
            "Hey guys, this is gonna be awesome lol", profile
        )
        assert score.score <= 0.8
        assert len(score.issues) > 0

    def test_professional_content(self):
        profile = create_default_profile("Brand")
        profile.tone = "professional"
        score = self.checker.check(
            "Our strategy leverages data-driven insights to optimize ROI.", profile
        )
        assert score.score >= 0.7

    def test_check_count(self):
        profile = create_default_profile("Brand")
        self.checker.check("Test content.", profile)
        assert self.checker.check_count == 1


# ── VocabularyChecker Tests ──

class TestVocabularyChecker:
    def setup_method(self):
        self.checker = VocabularyChecker()

    def test_clean_content(self):
        profile = create_default_profile("Brand")
        profile.forbidden_words = ["spam", "cheap"]
        score = self.checker.check("Professional content about innovation.", profile)
        assert score.score == 1.0

    def test_forbidden_word_detected(self):
        profile = create_default_profile("Brand")
        profile.forbidden_words = ["spam", "cheap"]
        score = self.checker.check("This is spam content.", profile)
        assert score.score <= 0.8
        assert any(i.category == "vocabulary" for i in score.issues)

    def test_preferred_word_used(self):
        profile = create_default_profile("Brand")
        profile.preferred_words = ["innovative", "cutting-edge"]
        score = self.checker.check("Our innovative solution transforms industries.", profile)
        assert score.score >= 0.7

    def test_terminology_enforcement(self):
        profile = create_default_profile("Brand")
        profile.terminology = {"AI agent": "autonomous agent"}
        score = self.checker.check("We build an AI agent for automation.", profile)
        assert any(i.category == "terminology" for i in score.issues)

    def test_check_count(self):
        profile = create_default_profile("Brand")
        self.checker.check("Test.", profile)
        assert self.checker.check_count == 1


# ── StyleAnalyzer Tests ──

class TestStyleAnalyzer:
    def setup_method(self):
        self.checker = StyleAnalyzer()

    def test_no_emoji_when_none_style(self):
        profile = create_default_profile("Brand")
        profile.emoji_style = "none"
        score = self.checker.check("Professional content. 🎉", profile)
        assert any(i.category == "emoji" for i in score.issues)

    def test_emoji_fine_when_moderate(self):
        profile = create_default_profile("Brand")
        profile.emoji_style = "moderate"
        score = self.checker.check("Great news! 🎉 Excited to share.", profile)
        assert not any(i.severity == "critical" for i in score.issues)

    def test_hashtag_style_branded(self):
        profile = create_default_profile("TestBrand")
        profile.hashtag_style = "branded"
        score = self.checker.check("Content #tech #news", profile)
        assert any(i.category == "hashtag_style" for i in score.issues)

    def test_hashtag_none_style(self):
        profile = create_default_profile("Brand")
        profile.hashtag_style = "none"
        score = self.checker.check("Content #hashtag", profile)
        assert any(i.category == "hashtag_style" for i in score.issues)

    def test_cta_detection(self):
        profile = create_default_profile("Brand")
        profile.cta_style = "soft"
        profile.preferred_ctas = ["learn more", "get started"]
        score = self.checker.check("Check out our platform. Learn more.", profile)
        assert not any(i.category == "cta" for i in score.issues)

    def test_sentence_length_check(self):
        profile = create_default_profile("Brand")
        profile.sentence_length_range = (5, 10)
        long_sentence = " ".join(["word"] * 30) + "."
        score = self.checker.check(long_sentence, profile)
        assert any(i.category == "sentence_length" for i in score.issues)

    def test_check_count(self):
        profile = create_default_profile("Brand")
        self.checker.check("Test.", profile)
        assert self.checker.check_count == 1


# ── BrandVoiceEngine Tests ──

class TestBrandVoiceEngine:
    def setup_method(self):
        self.engine = BrandVoiceEngine()

    def test_check_default_profile(self):
        report = self.engine.check("Professional content about AI.")
        assert isinstance(report, VoiceReport)
        assert report.overall_score >= 0.0

    def test_check_custom_profile(self):
        profile = create_default_profile("TechBrand")
        profile.tone = "formal"
        profile.forbidden_words = ["spam"]
        report = self.engine.check("Furthermore, our analysis shows growth.", profile)
        assert report.brand_name == "TechBrand"

    def test_check_quick(self):
        result = self.engine.check_quick("Professional AI content.")
        assert "overall_score" in result
        assert "is_consistent" in result

    def test_check_batch(self):
        reports = self.engine.check_batch(["Content A.", "Content B."])
        assert len(reports) == 2

    def test_statistics_populated(self):
        report = self.engine.check("Test content.")
        assert "check_time_ms" in report.statistics

    def test_check_count(self):
        self.engine.check("Test 1")
        self.engine.check("Test 2")
        assert self.engine.check_count == 2

    def test_report_to_dict(self):
        report = self.engine.check("Test content.")
        d = report.to_dict()
        assert "overall_score" in d
        assert "component_scores" in d

    def test_component_scores_populated(self):
        report = self.engine.check("Test content.")
        assert len(report.component_scores) >= 3

    def test_voice_report_compute_overall(self):
        report = VoiceReport("Test")
        report.component_scores.append(VoiceComponentScore("tone", 0.9))
        report.component_scores.append(VoiceComponentScore("vocab", 0.8))
        report.compute_overall()
        assert report.overall_score > 0

    def test_voice_report_no_components(self):
        report = VoiceReport("Test")
        report.compute_overall()
        assert report.overall_score == 0.5
