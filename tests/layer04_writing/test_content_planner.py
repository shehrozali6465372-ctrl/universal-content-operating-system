"""Tests for Layer 4 Module 1 — Content Planner (production-grade)."""
from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.content_planner.goal_analyzer import GoalAnalyzer
from layers.layer04_writing.modules.content_planner.audience_analyzer import AudienceAnalyzer
from layers.layer04_writing.modules.content_planner.platform_planner import PlatformPlanner, PlatformConstraints
from layers.layer04_writing.modules.content_planner.tone_selector import ToneSelector
from layers.layer04_writing.modules.content_planner.content_structure import ContentStructureBuilder
from layers.layer04_writing.modules.content_planner.constraint_manager import ConstraintManager
from layers.layer04_writing.modules.content_planner.plan_validator import PlanValidator
from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager, PlannerResult


# ── WritingPlan ──

class TestWritingPlan:
    def test_create_basic(self):
        plan = WritingPlan(topic="AI Jobs")
        assert plan.topic == "AI Jobs"
        assert plan.goal == "educate"
        assert plan.platform == "facebook"

    def test_to_dict(self):
        plan = WritingPlan(topic="Crypto")
        d = plan.to_dict()
        assert d["topic"] == "Crypto"
        assert "plan_id" in d

    def test_from_dict(self):
        data = {"topic": "AI", "goal": "entertain", "platform": "linkedin"}
        plan = WritingPlan.from_dict(data)
        assert plan.topic == "AI"
        assert plan.goal == "entertain"
        assert plan.platform == "linkedin"

    def test_is_valid(self):
        plan = WritingPlan(topic="AI")
        assert plan.is_valid is True

    def test_is_valid_empty(self):
        plan = WritingPlan()
        assert plan.is_valid is False

    def test_version_starts_at_1(self):
        plan = WritingPlan(topic="test")
        assert plan.version == 1


# ── GoalAnalyzer ──

class TestGoalAnalyzer:
    def setup_method(self):
        self.ga = GoalAnalyzer()

    def test_detect_educate(self):
        r = self.ga.analyze("How to learn Python programming")
        assert r.primary_goal == "educate"
        assert r.confidence > 0

    def test_detect_entertain(self):
        r = self.ga.analyze("Funny cat meme video viral")
        assert r.primary_goal == "entertain"

    def test_detect_promote(self):
        r = self.ga.analyze("Product launch discount offer buy now")
        assert r.primary_goal == "promote"

    def test_user_override(self):
        r = self.ga.analyze("AI", user_goal="inspire")
        assert r.primary_goal == "inspire"
        assert r.confidence == 0.9

    def test_secondary_goals(self):
        r = self.ga.analyze("AI tutorial guide")
        assert len(r.secondary_goals) >= 1

    def test_content_direction(self):
        r = self.ga.analyze("Crypto trading guide")
        assert "Crypto" in r.content_direction

    def test_to_dict(self):
        r = self.ga.analyze("test")
        d = r.to_dict()
        assert "primary_goal" in d
        assert "confidence" in d

    def test_goal_history(self):
        self.ga.analyze("A", user_goal="educate")
        self.ga.analyze("B", user_goal="entertain")
        assert len(self.ga.goal_history) == 2


# ── AudienceAnalyzer ──

class TestAudienceAnalyzer:
    def setup_method(self):
        self.aa = AudienceAnalyzer()

    def test_explicit_audience(self):
        r = self.aa.analyze("AI", audience_hint="students")
        assert r.audience_type == "students"
        assert r.confidence == 0.85

    def test_detect_tech(self):
        r = self.aa.analyze("Python code API algorithm")
        assert r.audience_type == "tech_enthusiasts"

    def test_detect_general(self):
        r = self.aa.analyze("nice weather today")
        assert r.audience_type == "general"

    def test_recommendations(self):
        r = self.aa.analyze("AI", audience_hint="professionals")
        assert r.recommended_tone == "professional"
        assert r.recommended_length == "long"

    def test_to_dict(self):
        r = self.aa.analyze("test")
        d = r.to_dict()
        assert "audience_type" in d

    def test_analysis_count(self):
        self.aa.analyze("A")
        self.aa.analyze("B")
        assert self.aa.analysis_count == 2


# ── PlatformPlanner ──

class TestPlatformPlanner:
    def setup_method(self):
        self.pp = PlatformPlanner()

    def test_get_constraints(self):
        c = self.pp.get_constraints("facebook")
        assert isinstance(c, PlatformConstraints)
        assert c.platform == "facebook"

    def test_recommended_length(self):
        c = self.pp.get_constraints("twitter")
        assert c.recommended_length == 200

    def test_recommend(self):
        rec = self.pp.recommend("facebook", "educate")
        assert rec["platform"] == "facebook"
        assert "best_practices" in rec

    def test_validate_length_ok(self):
        v = self.pp.validate_length("twitter", 100)
        assert v["valid"] is True

    def test_validate_length_too_long(self):
        v = self.pp.validate_length("twitter", 5000)
        assert v["valid"] is False

    def test_supported_platforms(self):
        assert "facebook" in self.pp.supported_platforms
        assert "twitter" in self.pp.supported_platforms

    def test_to_dict(self):
        c = self.pp.get_constraints("linkedin")
        d = c.to_dict()
        assert "max_length" in d


# ── ToneSelector ──

class TestToneSelector:
    def setup_method(self):
        self.ts = ToneSelector()

    def test_select_educate(self):
        r = self.ts.select(goal="educate")
        assert r.selected_tone in ("friendly", "informative", "professional")

    def test_select_override(self):
        r = self.ts.select(goal="educate", override="playful")
        assert r.selected_tone == "playful"
        assert r.confidence == 0.95

    def test_select_professional_audience(self):
        r = self.ts.select(goal="educate", audience="professionals")
        assert r.selected_tone == "professional"

    def test_available_tones(self):
        assert len(self.ts.available_tones) >= 5

    def test_get_profile(self):
        p = self.ts.get_profile("friendly")
        assert "formality" in p

    def test_to_dict(self):
        r = self.ts.select()
        d = r.to_dict()
        assert "selected_tone" in d

    def test_alternatives(self):
        r = self.ts.select(goal="educate")
        assert len(r.alternatives) >= 0


# ── ContentStructureBuilder ──

class TestContentStructureBuilder:
    def setup_method(self):
        self.cb = ContentStructureBuilder()

    def test_build_educational(self):
        s = self.cb.build(goal="educate")
        assert "hook" in s.sections
        assert s.total_estimated_words > 0

    def test_build_carousel(self):
        s = self.cb.build(goal="educate", content_type="carousel")
        assert s.template_name == "carousel"

    def test_build_story(self):
        s = self.cb.build(goal="educate", content_type="story")
        assert s.template_name == "story"

    def test_custom_sections(self):
        s = self.cb.build(goal="educate", custom_sections=["intro", "body", "outro"])
        assert len(s.custom_sections) == 3

    def test_to_dict(self):
        s = self.cb.build()
        d = s.to_dict()
        assert "sections" in d

    def test_available_templates(self):
        assert len(self.cb.get_available_templates()) >= 5


# ── ConstraintManager ──

class TestConstraintManager:
    def setup_method(self):
        self.cm = ConstraintManager()

    def test_add_and_get(self):
        self.cm.add("platform", "must", "facebook")
        c = self.cm.get("platform")
        assert c is not None
        assert c.value == "facebook"

    def test_remove(self):
        self.cm.add("x", "must", 1)
        assert self.cm.remove("x") is True
        assert self.cm.remove("x") is False

    def test_check_pass(self):
        self.cm.add("platform", "must", "facebook")
        violations = self.cm.check({"platform": "facebook"})
        assert len(violations) == 0

    def test_check_fail(self):
        self.cm.add("platform", "must", "facebook")
        violations = self.cm.check({"platform": "twitter"})
        assert len(violations) == 1

    def test_count(self):
        self.cm.add("a", "must", 1)
        self.cm.add("b", "should", 2)
        assert self.cm.count() == 2

    def test_clear(self):
        self.cm.add("a", "must", 1)
        self.cm.clear()
        assert self.cm.count() == 0


# ── PlanValidator ──

class TestPlanValidator:
    def setup_method(self):
        self.pv = PlanValidator()

    def test_valid_plan(self):
        plan = WritingPlan(topic="AI")
        r = self.pv.validate(plan)
        assert r.is_valid is True

    def test_invalid_goal(self):
        plan = WritingPlan(topic="AI")
        plan.goal = "invalid"
        r = self.pv.validate(plan)
        assert r.is_valid is False

    def test_invalid_platform(self):
        plan = WritingPlan(topic="AI")
        plan.platform = "myspace"
        r = self.pv.validate(plan)
        assert r.is_valid is False

    def test_empty_topic(self):
        plan = WritingPlan()
        r = self.pv.validate(plan)
        assert r.is_valid is False

    def test_warnings_for_uncommon_tone(self):
        plan = WritingPlan(topic="AI")
        plan.tone = "robotic"
        r = self.pv.validate(plan)
        assert len(r.warnings) >= 1

    def test_quick_check(self):
        plan = WritingPlan(topic="AI")
        assert self.pv.quick_check(plan) is True
        bad = WritingPlan()
        assert self.pv.quick_check(bad) is False

    def test_to_dict(self):
        plan = WritingPlan(topic="AI")
        r = self.pv.validate(plan)
        d = r.to_dict()
        assert "valid" in d
        assert "score" in d


# ── PlannerManager ──

class TestPlannerManager:
    def setup_method(self):
        self.pm = PlannerManager()

    def test_create_plan_basic(self):
        r = self.pm.create_plan("AI Jobs")
        assert isinstance(r, PlannerResult)
        assert r.plan is not None
        assert r.plan.topic == "AI Jobs"

    def test_create_plan_with_intel(self):
        intel = {"intent": "educate", "expected_engagement": 0.8}
        r = self.pm.create_plan("AI", intelligence_data=intel)
        assert r.goal_analysis is not None

    def test_create_plan_user_goal(self):
        r = self.pm.create_plan("Crypto", user_goal="entertain")
        assert r.plan.goal == "entertain"

    def test_create_plan_platform(self):
        r = self.pm.create_plan("AI", platform="twitter")
        assert r.plan.platform == "twitter"

    def test_create_plan_audience(self):
        r = self.pm.create_plan("AI", audience_hint="students")
        assert r.plan.audience == "students"

    def test_create_plan_tone_override(self):
        r = self.pm.create_plan("AI", tone_override="professional")
        assert r.plan.tone == "professional"

    def test_create_plan_validation(self):
        r = self.pm.create_plan("AI")
        assert r.validation is not None
        assert r.validation.is_valid is True

    def test_create_plan_structure(self):
        r = self.pm.create_plan("AI")
        assert r.structure is not None
        assert len(r.structure.sections) > 0

    def test_update_plan(self):
        r = self.pm.create_plan("AI")
        updated = self.pm.update_plan(r.plan, {"tone": "playful"})
        assert updated.plan.tone == "playful"
        assert updated.plan.version == 2

    def test_validate_plan(self):
        r = self.pm.create_plan("AI")
        v = self.pm.validate_plan(r.plan)
        assert v.is_valid is True

    def test_export_plan(self):
        r = self.pm.create_plan("AI")
        exported = self.pm.export_plan(r.plan)
        assert "topic" in exported

    def test_import_plan(self):
        data = {"topic": "Crypto", "goal": "promote", "platform": "linkedin"}
        plan = self.pm.import_plan(data)
        assert plan.topic == "Crypto"
        assert plan.goal == "promote"

    def test_plan_count(self):
        self.pm.create_plan("A")
        self.pm.create_plan("B")
        assert self.pm.plan_count == 2

    def test_pipeline_time(self):
        r = self.pm.create_plan("AI")
        assert r.pipeline_time_ms >= 0

    def test_to_dict(self):
        r = self.pm.create_plan("AI")
        d = r.to_dict()
        assert "plan" in d
        assert "validation" in d

    def test_create_plan_all_platforms(self):
        for platform in ("facebook", "instagram", "twitter", "linkedin", "youtube"):
            r = self.pm.create_plan("AI", platform=platform)
            assert r.plan.platform == platform

    def test_strategy_field(self):
        plan = WritingPlan(topic="AI")
        plan.strategy = "storytelling"
        d = plan.to_dict()
        assert d["strategy"] == "storytelling"

    def test_strategy_from_dict(self):
        data = {"topic": "AI", "strategy": "debate"}
        plan = WritingPlan.from_dict(data)
        assert plan.strategy == "debate"

