"""Tests for Layer 6 Module 3 — Safety & Policy Checker."""
from layers.layer06_quality.modules.safety_policy_checker.harmful_content_detector import HarmfulContentDetector
from layers.layer06_quality.modules.safety_policy_checker.spam_detector import SpamDetector
from layers.layer06_quality.modules.safety_policy_checker.platform_policy_checker import PlatformPolicyChecker
from layers.layer06_quality.modules.safety_policy_checker.safety_engine import SafetyEngine
from layers.layer06_quality.modules.safety_policy_checker.safety_report import SafetyReport, SafetyFlag


# ── HarmfulContentDetector Tests ──

class TestHarmfulContentDetector:
    def setup_method(self):
        self.detector = HarmfulContentDetector()

    def test_clean_content(self):
        flags = self.detector.detect("AI technology is transforming the world.")
        assert isinstance(flags, list)
        assert len(flags) == 0

    def test_empty_text(self):
        flags = self.detector.detect("")
        assert flags == []

    def test_threat_detection(self):
        flags = self.detector.detect("I will kill you tonight.")
        assert any(f.category == "violence" for f in flags)

    def test_dehumanization_detection(self):
        flags = self.detector.detect("These animals deserve to die.")
        assert any(f.category == "hate" for f in flags)

    def test_supremacy_detection(self):
        flags = self.detector.detect("The master race ideology is dangerous.")
        assert any(f.category == "hate" for f in flags)

    def test_self_harm_detection(self):
        flags = self.detector.detect("They glorify self-harm on social media.")
        assert any(f.category == "self_harm" for f in flags)

    def test_harassment_detection(self):
        flags = self.detector.detect("You are stupid and worthless.")
        assert any(f.category == "harassment" for f in flags)

    def test_gosy_detection(self):
        flags = self.detector.detect("Go die yourself, nobody cares about you.")
        assert any(f.category == "harassment" for f in flags)

    def test_discrimination_detection(self):
        flags = self.detector.detect("All immigrants should be banned from the country.")
        assert any(f.category == "discrimination" for f in flags)

    def test_detect_category(self):
        flags = self.detector.detect_category(
            "I will kill you tonight.", "violence"
        )
        assert len(flags) >= 1
        assert all(f.category == "violence" for f in flags)

    def test_has_critical_issues(self):
        clean = self.detector.detect("Hello world")
        assert not self.detector.has_critical_issues(clean)
        harmful = self.detector.detect("I will kill you and murder your family.")
        assert self.detector.has_critical_issues(harmful)

    def test_sensitivity_affects_results(self):
        strict = HarmfulContentDetector(sensitivity=0.1)
        loose = HarmfulContentDetector(sensitivity=0.9)
        text = "You are stupid and worthless."
        strict_flags = strict.detect(text)
        loose_flags = loose.detect(text)
        assert len(strict_flags) >= len(loose_flags)

    def test_confidence_range(self):
        flags = self.detector.detect("I will kill you.")
        for f in flags:
            assert 0.0 <= f.confidence <= 1.0

    def test_severity_classification(self):
        flags = self.detector.detect("I will kill you and murder your family.")
        for f in flags:
            assert f.severity in ("critical", "high", "medium", "low")

    def test_check_count(self):
        self.detector.detect("Hello")
        self.detector.detect("World")
        assert self.detector.check_count == 2

    def test_to_dict(self):
        flags = self.detector.detect("I will kill you.")
        for f in flags:
            d = f.to_dict()
            assert "category" in d
            assert "severity" in d
            assert "confidence" in d


# ── SpamDetector Tests ──

class TestSpamDetector:
    def setup_method(self):
        self.detector = SpamDetector()

    def test_clean_content(self):
        flags = self.detector.detect("AI technology is transforming the world.")
        assert isinstance(flags, list)

    def test_clickbait_detection(self):
        flags = self.detector.detect("You won't believe this one trick doctors hate!")
        assert any(f.subcategory == "clickbait" for f in flags)

    def test_spammy_phrase_detection(self):
        flags = self.detector.detect("Buy now! Limited time offer! Act now!")
        assert any(f.subcategory == "spammy_phrase" for f in flags)

    def test_excessive_caps(self):
        flags = self.detector.detect("THIS IS AMAZING NEWS EVERYONE MUST READ THIS NOW")
        assert any(f.subcategory == "excessive_caps" for f in flags)

    def test_excessive_exclamation(self):
        flags = self.detector.detect("Great news!!! amazing!!! wow!!! incredible!!!")
        assert any(f.subcategory == "excessive_punctuation" for f in flags)

    def test_excessive_question_marks(self):
        flags = self.detector.detect("Really?? How?? When?? Where?? Why??")
        assert any(f.subcategory == "excessive_punctuation" for f in flags)

    def test_repetition_detection(self):
        flags = self.detector.detect("This is is is a repeated word problem.")
        assert any(f.subcategory == "repetition" for f in flags)

    def test_urgency_manipulation(self):
        flags = self.detector.detect("Today only! Don't wait, last chance to buy!")
        assert any(f.subcategory == "urgency_manipulation" for f in flags)

    def test_misleading_claim(self):
        flags = self.detector.detect("This product is guaranteed to make $5000 per day!")
        assert any(f.subcategory == "misleading_claim" for f in flags)

    def test_check_count(self):
        self.detector.detect("Test 1")
        self.detector.detect("Test 2")
        assert self.detector.check_count == 2


# ── PlatformPolicyChecker Tests ──

class TestPlatformPolicyChecker:
    def setup_method(self):
        self.checker = PlatformPolicyChecker()

    def test_facebook_normal(self):
        result = self.checker.check("Hello world, this is a post.", "facebook")
        assert result.platform == "facebook"
        assert result.is_compliant

    def test_twitter_too_long(self):
        long_text = "A" * 281
        result = self.checker.check(long_text, "twitter")
        assert not result.is_compliant

    def test_twitter_short_ok(self):
        result = self.checker.check("Short tweet!", "twitter")
        assert result.is_compliant

    def test_linkedin_professional(self):
        result = self.checker.check("Professional post about AI trends.", "linkedin")
        assert result.is_compliant

    def test_check_batch(self):
        results = self.checker.check_batch("Hello", ["facebook", "twitter", "linkedin"])
        assert len(results) == 3

    def test_check_all_platforms(self):
        results = self.checker.check_all_platforms("Hello world")
        assert len(results) >= 7

    def test_get_compliant_platforms(self):
        results = self.checker.check_all_platforms("Short post.")
        compliant = self.checker.get_compliant_platforms(results)
        assert isinstance(compliant, list)

    def test_unknown_platform(self):
        result = self.checker.check("Hello", "myspace")
        assert result.platform == "myspace"
        assert any("unknown_platform" in i for i in result.issues)

    def test_hashtag_limit_twitter(self):
        tags = " ".join(f"#tag{i}" for i in range(10))
        result = self.checker.check(tags, "twitter")
        assert any(f.subcategory == "too_many_hashtags" for f in result.flags)

    def test_hashtag_not_allowed_reddit(self):
        result = self.checker.check("Post with #hashtags", "reddit")
        assert any(f.subcategory == "hashtags_not_allowed" for f in result.flags)

    def test_mention_limit(self):
        mentions = " ".join(f"@user{i}" for i in range(10))
        result = self.checker.check(mentions, "facebook")
        assert any(f.subcategory == "too_many_mentions" for f in result.flags)

    def test_mentions_not_allowed_pinterest(self):
        result = self.checker.check("Hello @someone", "pinterest")
        assert any(f.subcategory == "mentions_not_allowed" for f in result.flags)

    def test_check_count(self):
        self.checker.check("Test", "facebook")
        assert self.checker.check_count == 1

    def test_to_dict(self):
        result = self.checker.check("Hello", "facebook")
        d = result.to_dict()
        assert "platform" in d
        assert "is_compliant" in d
        assert "score" in d


# ── SafetyEngine Tests ──

class TestSafetyEngine:
    def setup_method(self):
        self.engine = SafetyEngine()

    def test_safe_content(self):
        report = self.engine.check("AI technology is transforming the world.")
        assert isinstance(report, SafetyReport)
        assert report.overall_safe

    def test_harmful_content(self):
        report = self.engine.check("I will kill you and murder everyone.")
        assert not report.overall_safe

    def test_with_platform_check(self):
        report = self.engine.check(
            "Professional post about AI.", platforms=["facebook", "linkedin"]
        )
        assert len(report.policy_results) == 2

    def test_check_quick(self):
        result = self.engine.check_quick("AI is growing fast.")
        assert "overall_safe" in result
        assert "overall_score" in result

    def test_check_batch(self):
        reports = self.engine.check_batch(["Hello", "World"])
        assert len(reports) == 2

    def test_spam_detection_in_pipeline(self):
        report = self.engine.check(
            "BUY NOW!!! YOU WON'T BELIEVE THIS!!! ACT NOW!!!"
        )
        assert len(report.spam_flags) >= 1

    def test_statistics_populated(self):
        report = self.engine.check("Test content.")
        assert "check_time_ms" in report.statistics
        assert "content_length" in report.statistics

    def test_check_count(self):
        self.engine.check("Test 1")
        self.engine.check("Test 2")
        assert self.engine.check_count == 2

    def test_compute_overall_no_flags(self):
        report = SafetyReport()
        report.compute_overall()
        assert report.overall_safe

    def test_compute_overall_critical_flag(self):
        report = SafetyReport()
        report.add_flag(SafetyFlag(severity="critical"))
        report.compute_overall()
        assert not report.overall_safe

    def test_compute_overall_many_high_flags(self):
        report = SafetyReport()
        for _ in range(4):
            report.add_flag(SafetyFlag(severity="high"))
        report.compute_overall()
        assert not report.overall_safe

    def test_report_to_dict(self):
        report = self.engine.check("Test content.")
        d = report.to_dict()
        assert "overall_safe" in d
        assert "flags" in d
        assert "statistics" in d
