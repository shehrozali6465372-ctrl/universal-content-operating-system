"""Tests for Layer 7 Module 9 — Publishing Policies."""
from layers.layer07_publishing.modules.publishing_policies.platform_rules import PlatformRules, PlatformRule
from layers.layer07_publishing.modules.publishing_policies.content_limits import ContentLimits
from layers.layer07_publishing.modules.publishing_policies.rate_limiter import RateLimiter, RateLimitConfig
from layers.layer07_publishing.modules.publishing_policies.media_policies import MediaPolicies, MediaPolicy
from layers.layer07_publishing.modules.publishing_policies.schedule_policies import SchedulePolicies, SchedulePolicy
from layers.layer07_publishing.modules.publishing_policies.content_safety import ContentSafety, SafetyRule
from layers.layer07_publishing.modules.publishing_policies.api_versions import APIVersionManager, APIVersion
from layers.layer07_publishing.modules.publishing_policies.brand_safety import BrandSafety, BrandPolicy
from layers.layer07_publishing.modules.publishing_policies.policy_validator import PolicyValidator, ValidationResult
from layers.layer07_publishing.modules.publishing_policies.policy_manager import PolicyManager, PolicyReport
from layers.layer07_publishing.modules.publishing_policies.exceptions import (
    PolicyError, PolicyViolationError, PolicyNotFoundError,
)


# ─── PlatformRules Tests ─────────────────────────────────────────────
class TestPlatformRule:
    def test_create(self):
        r = PlatformRule("r1", "facebook", "content_length", "Max length")
        assert r.rule_id == "r1"
        assert r.enabled is True

    def test_to_dict(self):
        r = PlatformRule("r1", "fb", "test", "desc")
        d = r.to_dict()
        assert d["rule_id"] == "r1"
        assert d["version"] == "1.0.0"


class TestPlatformRules:
    def setup_method(self):
        self.pr = PlatformRules()

    def test_get_rules(self):
        rules = self.pr.get_rules("facebook")
        assert len(rules) >= 1

    def test_add_rule(self):
        rule = PlatformRule("custom_1", "discord", "content_length", "Discord limit")
        self.pr.add_rule(rule)
        assert "discord" in self.pr.get_all_platforms()

    def test_get_rule(self):
        rule = self.pr.get_rule("fb_text")
        assert rule is not None
        assert rule.platform == "facebook"

    def test_get_rule_not_found(self):
        assert self.pr.get_rule("nonexistent") is None

    def test_get_all_platforms(self):
        platforms = self.pr.get_all_platforms()
        assert "facebook" in platforms
        assert "instagram" in platforms

    def test_remove_rule(self):
        self.pr.add_rule(PlatformRule("to_remove", "test", "type", "desc"))
        self.pr.remove_rule("to_remove")
        assert self.pr.get_rule("to_remove") is None

    def test_get_rules_count(self):
        assert self.pr.get_rules_count("facebook") >= 1
        assert self.pr.get_rules_count() > 0


# ─── ContentLimits Tests ─────────────────────────────────────────────
class TestContentLimits:
    def setup_method(self):
        self.cl = ContentLimits()

    def test_get_limits(self):
        limits = self.cl.get_limits("facebook")
        assert "max_text_length" in limits
        assert limits["max_text_length"] == 63206

    def test_get_limit(self):
        assert self.cl.get_limit("twitter", "max_text_length") == 280

    def test_set_limit(self):
        self.cl.set_limit("custom", "max_length", 5000)
        assert self.cl.get_limit("custom", "max_length") == 5000

    def test_check_text_length_ok(self):
        assert self.cl.check_text_length("twitter", "Hi") is True

    def test_check_text_length_fail(self):
        assert self.cl.check_text_length("twitter", "x" * 300) is False

    def test_check_image_count_ok(self):
        assert self.cl.check_image_count("instagram", 5) is True

    def test_check_image_count_fail(self):
        assert self.cl.check_image_count("instagram", 15) is False

    def test_check_hashtag_count_ok(self):
        assert self.cl.check_hashtag_count("linkedin", 3) is True

    def test_check_hashtag_count_fail(self):
        assert self.cl.check_hashtag_count("linkedin", 10) is False

    def test_get_supported_platforms(self):
        platforms = self.cl.get_supported_platforms()
        assert "facebook" in platforms
        assert len(platforms) >= 6


# ─── RateLimiter Tests ───────────────────────────────────────────────
class TestRateLimitConfig:
    def test_create(self):
        c = RateLimitConfig("facebook")
        assert c.platform == "facebook"
        assert c.posts_per_day == 25

    def test_to_dict(self):
        c = RateLimitConfig("fb")
        d = c.to_dict()
        assert d["platform"] == "fb"


class TestRateLimiter:
    def setup_method(self):
        self.rl = RateLimiter()

    def test_can_publish(self):
        assert self.rl.can_publish("facebook") is True

    def test_record_publish(self):
        self.rl.record_publish("facebook")
        assert self.rl.get_remaining("facebook") == 24

    def test_get_remaining(self):
        assert self.rl.get_remaining("facebook") == 25
        self.rl.record_publish("facebook")
        assert self.rl.get_remaining("facebook") == 24

    def test_set_config(self):
        config = RateLimitConfig("custom")
        config.posts_per_day = 5
        self.rl.set_config("custom", config)
        assert self.rl.get_remaining("custom") == 5

    def test_get_all_configs(self):
        configs = self.rl.get_all_configs()
        assert "facebook" in configs

    def test_unknown_platform(self):
        assert self.rl.can_publish("unknown") is True
        assert self.rl.get_remaining("unknown") == 999


# ─── MediaPolicies Tests ─────────────────────────────────────────────
class TestMediaPolicy:
    def test_create(self):
        p = MediaPolicy("facebook")
        assert p.platform == "facebook"
        assert "jpg" in p.supported_image_formats

    def test_to_dict(self):
        p = MediaPolicy("fb")
        d = p.to_dict()
        assert d["platform"] == "fb"


class TestMediaPolicies:
    def setup_method(self):
        self.mp = MediaPolicies()

    def test_get_policy(self):
        p = self.mp.get_policy("facebook")
        assert p.platform == "facebook"

    def test_check_image_format_ok(self):
        assert self.mp.check_image_format("facebook", "jpg") is True
        assert self.mp.check_image_format("facebook", "png") is True

    def test_check_image_format_fail(self):
        assert self.mp.check_image_format("facebook", "bmp") is False

    def test_check_video_format(self):
        assert self.mp.check_video_format("youtube", "mp4") is True

    def test_check_image_size_ok(self):
        assert self.mp.check_image_size("facebook", 5.0) is True

    def test_check_image_size_fail(self):
        assert self.mp.check_image_size("facebook", 15.0) is False

    def test_check_video_size(self):
        assert self.mp.check_video_size("youtube", 100.0) is True
        assert self.mp.check_video_size("youtube", 300.0) is False

    def test_get_all_policies(self):
        policies = self.mp.get_all_policies()
        assert len(policies) >= 6


# ─── SchedulePolicies Tests ──────────────────────────────────────────
class TestSchedulePolicy:
    def test_create(self):
        p = SchedulePolicy("facebook")
        assert p.supports_scheduling is True

    def test_to_dict(self):
        d = SchedulePolicy("fb").to_dict()
        assert "supports_scheduling" in d


class TestSchedulePolicies:
    def setup_method(self):
        self.sp = SchedulePolicies()

    def test_get_policy(self):
        p = self.sp.get_policy("facebook")
        assert p.platform == "facebook"

    def test_can_schedule(self):
        assert self.sp.can_schedule("facebook", 15) is True

    def test_can_schedule_too_soon(self):
        assert self.sp.can_schedule("facebook", 5) is False

    def test_is_valid_schedule_time(self):
        assert self.sp.is_valid_schedule_time("facebook", 12) is True

    def test_get_all_policies(self):
        policies = self.sp.get_all_policies()
        assert len(policies) >= 6


# ─── ContentSafety Tests ─────────────────────────────────────────────
class TestSafetyRule:
    def test_create(self):
        r = SafetyRule("r1", "hate_speech", "critical")
        assert r.enabled is True

    def test_to_dict(self):
        d = SafetyRule("r1", "spam", "high").to_dict()
        assert d["category"] == "spam"


class TestContentSafety:
    def setup_method(self):
        self.cs = ContentSafety()

    def test_check_content_safe(self):
        violations = self.cs.check_content("Hello world")
        assert len(violations) == 0

    def test_is_safe(self):
        assert self.cs.is_safe("Hello world") is True

    def test_get_rules(self):
        rules = self.cs.get_rules()
        assert len(rules) >= 6

    def test_get_rules_by_category(self):
        rules = self.cs.get_rules_by_category("hate_speech")
        assert len(rules) == 1

    def test_violation_count(self):
        assert self.cs.get_violation_count("Hello") == 0

    def test_add_rule(self):
        rule = SafetyRule("custom", "custom_category", "medium")
        self.cs.add_rule(rule)
        assert len(self.cs.get_rules()) >= 7


# ─── APIVersionManager Tests ─────────────────────────────────────────
class TestAPIVersion:
    def test_create(self):
        v = APIVersion("facebook")
        assert v.deprecated is False

    def test_to_dict(self):
        d = APIVersion("fb").to_dict()
        assert d["platform"] == "fb"


class TestAPIVersionManager:
    def setup_method(self):
        self.avm = APIVersionManager()

    def test_get_version(self):
        v = self.avm.get_version("facebook")
        assert v is not None
        assert v.platform == "facebook"

    def test_set_version(self):
        v = APIVersion("custom")
        v.current_version = "v2.0"
        self.avm.set_version("custom", v)
        assert self.avm.get_version("custom").current_version == "v2.0"

    def test_is_supported(self):
        assert self.avm.is_supported("facebook") is True

    def test_is_deprecated(self):
        assert self.avm.is_deprecated("facebook") is False

    def test_get_all_versions(self):
        versions = self.avm.get_all_versions()
        assert "facebook" in versions


# ─── BrandSafety Tests ───────────────────────────────────────────────
class TestBrandPolicy:
    def test_create(self):
        bp = BrandPolicy("brand_1")
        assert bp.brand_id == "brand_1"

    def test_to_dict(self):
        bp = BrandPolicy("b1")
        bp.blocked_topics = ["politics"]
        d = bp.to_dict()
        assert "politics" in d["blocked_topics"]


class TestBrandSafety:
    def setup_method(self):
        self.bs = BrandSafety()

    def test_add_policy(self):
        bp = BrandPolicy("brand_1")
        bp.blocked_topics = ["politics"]
        self.bs.add_policy(bp)
        assert self.bs.get_policy("brand_1").brand_id == "brand_1"

    def test_check_content_safe(self):
        bp = BrandPolicy("b1")
        bp.blocked_topics = ["politics"]
        self.bs.add_policy(bp)
        violations = self.bs.check_content("b1", "Hello world")
        assert len(violations) == 0

    def test_check_content_violation(self):
        bp = BrandPolicy("b1")
        bp.blocked_topics = ["politics"]
        self.bs.add_policy(bp)
        violations = self.bs.check_content("b1", "This is about politics")
        assert len(violations) == 1

    def test_check_competitor(self):
        bp = BrandPolicy("b1")
        bp.blocked_competitors = ["competitor_x"]
        self.bs.add_policy(bp)
        violations = self.bs.check_content("b1", "Check out competitor_x")
        assert len(violations) == 1

    def test_is_safe(self):
        bp = BrandPolicy("b1")
        bp.blocked_topics = ["politics"]
        self.bs.add_policy(bp)
        assert self.bs.is_safe("b1", "Hello") is True

    def test_get_all_policies(self):
        self.bs.add_policy(BrandPolicy("b1"))
        self.bs.add_policy(BrandPolicy("b2"))
        assert len(self.bs.get_all_policies()) == 2


# ─── PolicyValidator Tests ───────────────────────────────────────────
class TestValidationResult:
    def test_create(self):
        vr = ValidationResult("facebook")
        assert vr.passed is True

    def test_add_violation(self):
        vr = ValidationResult()
        vr.add_violation("Too long")
        assert vr.passed is False
        assert len(vr.violations) == 1

    def test_add_warning(self):
        vr = ValidationResult()
        vr.add_warning("Many hashtags")
        assert vr.passed is True
        assert len(vr.warnings) == 1

    def test_to_dict(self):
        vr = ValidationResult("fb")
        vr.add_violation("err")
        d = vr.to_dict()
        assert d["passed"] is False
        assert d["violation_count"] == 1


class TestPolicyValidator:
    def setup_method(self):
        self.pv = PolicyValidator()

    def test_validate_ok(self):
        result = self.pv.validate("facebook", "Hello world")
        assert result.passed is True

    def test_validate_text_too_long(self):
        result = self.pv.validate("twitter", "x" * 300)
        assert result.passed is False
        assert any("length" in v for v in result.violations)

    def test_validate_too_many_images(self):
        result = self.pv.validate("instagram", "Hi", image_count=15)
        assert result.passed is False

    def test_validate_brand_safety(self):
        self.pv.brand_safety.add_policy(BrandPolicy("b1"))
        result = self.pv.validate("facebook", "Hello", brand_id="b1")
        assert result.passed is True

    def test_validate_all_platforms(self):
        results = self.pv.validate_all_platforms("Hello")
        assert "facebook" in results
        assert "twitter" in results

    def test_validation_count(self):
        self.pv.validate("fb", "Hi")
        assert self.pv.validation_count == 1


# ─── PolicyManager Tests ─────────────────────────────────────────────
class TestPolicyReport:
    def test_create(self):
        r = PolicyReport("facebook")
        assert r.report_id.startswith("prpt_")
        assert r.api_supported is True

    def test_to_dict(self):
        r = PolicyReport("fb")
        d = r.to_dict()
        assert d["platform"] == "fb"


class TestPolicyManager:
    def setup_method(self):
        self.pm = PolicyManager()

    def test_validate_content(self):
        result = self.pm.validate_content("facebook", "Hello world")
        assert result.passed is True

    def test_validate_content_fail(self):
        result = self.pm.validate_content("twitter", "x" * 300)
        assert result.passed is False

    def test_is_publish_allowed(self):
        assert self.pm.is_publish_allowed("facebook") is True

    def test_record_publish(self):
        self.pm.record_publish("facebook")
        remaining = self.pm.rate_limiter.get_remaining("facebook")
        assert remaining == 24

    def test_get_platform_info(self):
        info = self.pm.get_platform_info("facebook")
        assert "limits" in info
        assert "rate_remaining" in info

    def test_get_all_platforms(self):
        platforms = self.pm.get_all_platforms()
        assert "facebook" in platforms
        assert len(platforms) >= 6

    def test_get_reports(self):
        self.pm.validate_content("facebook", "Hi")
        self.pm.validate_content("linkedin", "Hi")
        assert len(self.pm.get_reports()) == 2
        assert len(self.pm.get_reports("facebook")) == 1

    def test_report_count(self):
        self.pm.validate_content("fb", "Hi")
        assert self.pm.report_count == 1


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(PolicyError, Exception)
        assert issubclass(PolicyViolationError, PolicyError)
        assert issubclass(PolicyNotFoundError, PolicyError)

    def test_message(self):
        err = PolicyViolationError("content too long")
        assert str(err) == "content too long"
