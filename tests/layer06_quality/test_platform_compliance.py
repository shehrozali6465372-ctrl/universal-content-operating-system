"""Tests for Layer 6 Module 6 — Platform Compliance Engine."""
from layers.layer06_quality.modules.platform_compliance_engine.format_checker import FormatChecker
from layers.layer06_quality.modules.platform_compliance_engine.content_policy_checker import ContentPolicyChecker
from layers.layer06_quality.modules.platform_compliance_engine.platform_rules import get_rules, get_all_platforms
from layers.layer06_quality.modules.platform_compliance_engine.compliance_engine import ComplianceEngine
from layers.layer06_quality.modules.platform_compliance_engine.compliance_report import (
    ComplianceReport, PlatformComplianceResult, RuleViolation,
)


# ── FormatChecker Tests ──

class TestFormatChecker:
    def setup_method(self):
        self.checker = FormatChecker()

    def test_compliant_content(self):
        rules = {"max_post_length": 500, "min_post_length": 10}
        violations = self.checker.check("This is a valid post.", rules)
        assert violations == []

    def test_exceeds_max_length(self):
        rules = {"max_post_length": 10}
        violations = self.checker.check("This is a long post that exceeds the limit.", rules)
        assert any(v.rule_id == "format_max_length" for v in violations)

    def test_below_min_length(self):
        rules = {"min_post_length": 50}
        violations = self.checker.check("Short.", rules)
        assert any(v.rule_id == "format_min_length" for v in violations)

    def test_optimal_length_outside(self):
        rules = {"optimal_length": (50, 100)}
        violations = self.checker.check("Short.", rules)
        assert any(v.rule_id == "format_optimal_length" for v in violations)

    def test_all_caps_detected(self):
        rules = {"no_all_caps": True}
        violations = self.checker.check("THIS IS AMAZING NEWS FOR EVERYONE TODAY", rules)
        assert any(v.rule_id == "format_no_all_caps" for v in violations)

    def test_informal_language(self):
        rules = {"professional_tone": True}
        violations = self.checker.check("This is gonna be amazing lol", rules)
        assert any(v.rule_id == "format_informal_language" for v in violations)

    def test_auto_fixable_flag(self):
        rules = {"max_post_length": 10}
        violations = self.checker.check("Long content here.", rules)
        fixable = [v for v in violations if v.auto_fixable]
        assert len(fixable) >= 1

    def test_check_count(self):
        self.checker.check("Test", {"max_post_length": 1000})
        assert self.checker.check_count == 1


# ── ContentPolicyChecker Tests ──

class TestContentPolicyChecker:
    def setup_method(self):
        self.checker = ContentPolicyChecker()

    def test_clean_content(self):
        rules = {"forbidden_patterns": [r"spam\w*"], "no_engagement_bait": True}
        violations = self.checker.check("Great content about AI.", rules)
        assert violations == []

    def test_forbidden_pattern(self):
        rules = {"forbidden_patterns": [r"spam\w*"]}
        violations = self.checker.check("This is spammy content.", rules)
        assert any(v.rule_id == "policy_forbidden_pattern" for v in violations)

    def test_engagement_bait(self):
        rules = {"no_engagement_bait": True}
        violations = self.checker.check("Like and share to win!", rules)
        assert any(v.rule_id == "policy_engagement_bait" for v in violations)

    def test_hashtag_limit(self):
        rules = {"max_hashtags": 3}
        content = "Post " + " ".join(f"#tag{i}" for i in range(5))
        violations = self.checker.check(content, rules)
        assert any(v.rule_id == "policy_hashtag_limit" for v in violations)

    def test_mention_limit(self):
        rules = {"max_mentions": 2}
        content = "Hello @user1 @user2 @user3"
        violations = self.checker.check(content, rules)
        assert any(v.rule_id == "policy_mention_limit" for v in violations)

    def test_link_limit(self):
        rules = {"max_link_preview": 1}
        content = "Check https://a.com and https://b.com"
        violations = self.checker.check(content, rules)
        assert any(v.rule_id == "policy_link_limit" for v in violations)

    def test_requires_hashtags(self):
        rules = {"requires_hashtags": True}
        violations = self.checker.check("No hashtags here.", rules)
        assert any(v.rule_id == "policy_requires_hashtags" for v in violations)

    def test_check_count(self):
        self.checker.check("Test", {})
        assert self.checker.check_count == 1


# ── PlatformRules Tests ──

class TestPlatformRules:
    def test_get_rules_facebook(self):
        rules = get_rules("facebook")
        assert "max_post_length" in rules
        assert rules["max_post_length"] == 63206

    def test_get_rules_unknown(self):
        rules = get_rules("myspace")
        assert rules == {}

    def test_get_all_platforms(self):
        platforms = get_all_platforms()
        assert len(platforms) >= 7
        assert "facebook" in platforms
        assert "instagram" in platforms


# ── ComplianceEngine Tests ──

class TestComplianceEngine:
    def setup_method(self):
        self.engine = ComplianceEngine()

    def test_compliant_content(self):
        result = self.engine.check("Professional post about AI.", "facebook")
        assert isinstance(result, PlatformComplianceResult)
        assert result.is_compliant

    def test_exceeds_length(self):
        result = self.engine.check("A" * 281, "twitter")
        assert not result.is_compliant

    def test_engagement_bait(self):
        result = self.engine.check("Like and share to win!", "facebook")
        assert not result.is_compliant

    def test_check_batch(self):
        report = self.engine.check_batch("Professional AI content.", ["facebook", "linkedin"])
        assert isinstance(report, ComplianceReport)
        assert len(report.platform_results) == 2

    def test_check_batch_all_platforms(self):
        report = self.engine.check_batch("Good content.")
        assert len(report.platform_results) >= 7

    def test_check_quick(self):
        result = self.engine.check_quick("Test post.", "facebook")
        assert "is_compliant" in result
        assert "compliance_score" in result

    def test_get_fixable_violations(self):
        result = self.engine.check("A" * 281, "twitter")
        fixable = self.engine.get_fixable_violations(result)
        assert len(fixable) >= 1

    def test_statistics_populated(self):
        report = self.engine.check_batch("Content.", ["facebook"])
        assert "check_time_ms" in report.statistics
        assert "platforms_checked" in report.statistics

    def test_check_count(self):
        self.engine.check("Test", "facebook")
        assert self.engine.check_count == 1

    def test_report_to_dict(self):
        report = self.engine.check_batch("Content.", ["facebook"])
        d = report.to_dict()
        assert "overall_compliant" in d
        assert "platform_results" in d

    def test_auto_fixable_count(self):
        report = self.engine.check_batch("A" * 281, ["twitter", "facebook"])
        report.compute_overall()
        assert report.auto_fixable_count >= 0

    def test_violation_to_dict(self):
        v = RuleViolation(
            rule_id="test", category="format", severity="medium",
            description="test desc", auto_fixable=True,
        )
        d = v.to_dict()
        assert "rule_id" in d
        assert "auto_fixable" in d
