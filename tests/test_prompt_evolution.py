"""Tests for Prompt Evolution Engine — 7 files, comprehensive coverage."""
from __future__ import annotations
import os
import time
import tempfile
import pytest


# ══════════════════════════════════════════════════════════════════════
# PromptTemplate Tests
# ══════════════════════════════════════════════════════════════════════

class TestPromptTemplate:
    def test_create_default(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        assert tpl.template_id.startswith("tpl_")
        assert tpl.platform == "facebook"
        assert tpl.score == 0.0
        assert tpl.total_uses == 0

    def test_create_with_params(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI", platform="twitter", tone="casual", hook_type="statistic")
        assert tpl.topic == "AI"
        assert tpl.platform == "twitter"
        assert tpl.hook_type == "statistic"

    def test_invalid_hook_type_falls_back(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(hook_type="nonexistent")
        assert tpl.hook_type == "question"

    def test_invalid_cta_type_falls_back(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(cta_type="nonexistent")
        assert tpl.cta_type == "ask_question"

    def test_record_use_updates_metrics(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        tpl.record_use(impressions=100, engagements=20, clicks=5)
        assert tpl.total_uses == 1
        assert tpl.total_impressions == 100
        assert tpl.total_engagements == 20
        assert tpl.total_clicks == 5
        assert tpl.engagement_rate == 0.2
        assert tpl.click_rate == 0.05
        assert tpl.last_used_at is not None

    def test_score_calculation(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        tpl.record_use(impressions=1000, engagements=100, clicks=50)
        # engagement_rate=0.1, click_rate=0.05
        # base = 0.1*60 + 0.05*40 = 6 + 2 = 8
        # consistency = min(2.0, 1*0.1) = 0.1
        # score = 8.1
        assert tpl.score > 7.0

    def test_is_champion(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        tpl.record_use(impressions=10000, engagements=1000, clicks=500)
        assert tpl.is_champion is True

    def test_is_challenger(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        tpl.record_use(impressions=1000, engagements=100, clicks=20)
        assert tpl.is_challenger is True

    def test_is_retired(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        for _ in range(15):
            tpl.record_use(impressions=10, engagements=0, clicks=0)
        assert tpl.is_retired is True

    def test_clone(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI", platform="facebook")
        tpl.tags = ["test"]
        clone = tpl.clone()
        assert clone.template_id != tpl.template_id
        assert clone.topic == tpl.topic
        assert clone.parent_id == tpl.template_id
        assert clone.generation == 2
        assert "test" in clone.tags

    def test_to_dict(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI")
        d = tpl.to_dict()
        assert "template_id" in d
        assert d["topic"] == "AI"
        assert "score" in d
        assert "is_champion" in d


# ══════════════════════════════════════════════════════════════════════
# StyleLibrary Tests
# ══════════════════════════════════════════════════════════════════════

class TestStyleLibrary:
    def setup_method(self):
        from layers.layer09_learning.modules.prompt_evolution.style_library import StyleLibrary
        self.lib = StyleLibrary()

    def test_builtin_styles_exist(self):
        styles = self.lib.list_styles()
        assert len(styles) >= 8
        assert "facebook_educational" in styles
        assert "instagram_carousel" in styles
        assert "linkedin_thought_leadership" in styles

    def test_get_style(self):
        style = self.lib.get_style("facebook_educational")
        assert style["platform"] == "facebook"
        assert "hooks" in style
        assert "ctas" in style
        assert len(style["hooks"]) > 0

    def test_get_style_unknown_returns_default(self):
        style = self.lib.get_style("nonexistent_style")
        assert style["platform"] == "facebook"
        assert "hooks" in style

    def test_list_styles_by_platform(self):
        fb_styles = self.lib.list_styles(platform="facebook")
        assert all("facebook" in s for s in fb_styles)
        assert len(fb_styles) >= 2

    def test_add_custom_style(self):
        self.lib.add_style("my_custom", {"platform": "facebook", "hooks": ["Test hook"]})
        assert "my_custom" in self.lib.list_styles()

    def test_remove_custom_style(self):
        self.lib.add_style("removable", {"platform": "facebook"})
        assert self.lib.remove_style("removable") is True
        assert "removable" not in self.lib.list_styles()

    def test_cannot_remove_builtin(self):
        assert self.lib.remove_style("facebook_educational") is False

    def test_get_random_hook(self):
        hook = self.lib.get_random_hook("facebook_educational")
        assert isinstance(hook, str)
        assert len(hook) > 0

    def test_get_random_cta(self):
        cta = self.lib.get_random_cta("facebook_educational")
        assert isinstance(cta, str)
        assert len(cta) > 0

    def test_get_platform_styles(self):
        ig = self.lib.get_platform_styles("instagram")
        assert len(ig) >= 2

    def test_get_style_count(self):
        assert self.lib.get_style_count() >= 8


# ══════════════════════════════════════════════════════════════════════
# TemplateMemory Tests
# ══════════════════════════════════════════════════════════════════════

class TestTemplateMemory:
    def setup_method(self):
        from layers.layer09_learning.modules.prompt_evolution.template_memory import TemplateMemory
        self.memory = TemplateMemory()

    def test_store_and_get(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI", platform="facebook")
        tid = self.memory.store(tpl)
        assert tid == tpl.template_id
        retrieved = self.memory.get(tid)
        assert retrieved is not None
        assert retrieved.topic == "AI"

    def test_search_by_platform(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        self.memory.store(PromptTemplate(topic="t1", platform="facebook"))
        self.memory.store(PromptTemplate(topic="t2", platform="twitter"))
        results = self.memory.search(platform="facebook")
        assert len(results) == 1
        assert results[0].platform == "facebook"

    def test_search_by_topic(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        self.memory.store(PromptTemplate(topic="AI", platform="facebook"))
        self.memory.store(PromptTemplate(topic="Python", platform="facebook"))
        results = self.memory.search(topic="AI")
        assert len(results) == 1
        assert results[0].topic == "AI"

    def test_search_by_hook_type(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        self.memory.store(PromptTemplate(hook_type="question"))
        self.memory.store(PromptTemplate(hook_type="statistic"))
        results = self.memory.search(hook_type="question")
        assert len(results) == 1

    def test_search_by_score(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        low = PromptTemplate(topic="low")
        low.record_use(impressions=10, engagements=0, clicks=0)
        high = PromptTemplate(topic="high")
        high.record_use(impressions=100, engagements=50, clicks=20)
        self.memory.store(low)
        self.memory.store(high)
        results = self.memory.search(min_score=5.0)
        assert len(results) == 1
        assert results[0].topic == "high"

    def test_remove(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="remove_me")
        self.memory.store(tpl)
        assert self.memory.remove(tpl.template_id) is True
        assert self.memory.get(tpl.template_id) is None

    def test_remove_nonexistent(self):
        assert self.memory.remove("fake_id") is False

    def test_get_champions(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        champ = PromptTemplate(topic="champ")
        champ.record_use(impressions=10000, engagements=1000, clicks=500)
        self.memory.store(champ)
        champions = self.memory.get_champions()
        assert len(champions) >= 1

    def test_get_stats(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        self.memory.store(PromptTemplate(topic="a", platform="facebook"))
        self.memory.store(PromptTemplate(topic="b", platform="twitter"))
        stats = self.memory.get_stats()
        assert stats["total_templates"] == 2
        assert "facebook" in stats["platforms"]

    def test_max_entries_enforced(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        from layers.layer09_learning.modules.prompt_evolution.template_memory import TemplateMemory as TM
        small_memory = TM(max_entries=3)
        for i in range(5):
            tpl = PromptTemplate(topic=f"topic_{i}")
            tpl.record_use(impressions=100, engagements=i * 10, clicks=i * 2)
            small_memory.store(tpl)
        assert small_memory.get_stats()["total_templates"] <= 3

    def test_search_by_tags(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="tagged")
        tpl.tags = ["viral", "trending"]
        self.memory.store(tpl)
        results = self.memory.search(tags=["viral"])
        assert len(results) == 1


# ══════════════════════════════════════════════════════════════════════
# PerformanceTracker Tests
# ══════════════════════════════════════════════════════════════════════

class TestPerformanceTracker:
    def setup_method(self):
        from layers.layer09_learning.modules.prompt_evolution.performance_tracker import PerformanceTracker
        self.tracker = PerformanceTracker()

    def test_record_event(self):
        from layers.layer09_learning.modules.prompt_evolution.performance_tracker import PerformanceEvent
        event = self.tracker.record_event("tpl_1", "facebook", 100, 20, 5)
        assert event.impressions == 100
        assert event.engagements == 20
        assert self.tracker.get_event_count() == 1

    def test_record_post_published(self):
        self.tracker.record_post_published("tpl_1", "facebook", 500, 50, 10)
        stats = self.tracker.get_template_stats("tpl_1")
        assert stats["total_impressions"] == 500
        assert stats["engagement_rate"] == 0.1

    def test_record_update(self):
        self.tracker.record_update("tpl_1", "facebook", 300, 30, 8)
        stats = self.tracker.get_template_stats("tpl_1")
        assert stats["total_impressions"] == 300

    def test_template_stats(self):
        self.tracker.record_event("tpl_1", "facebook", 1000, 100, 50, 10)
        stats = self.tracker.get_template_stats("tpl_1")
        assert stats["total_impressions"] == 1000
        assert stats["engagement_rate"] == 0.1
        assert stats["click_rate"] == 0.05
        assert stats["conversion_rate"] == 0.01

    def test_platform_stats(self):
        self.tracker.record_event("tpl_1", "facebook", 500, 50, 10)
        self.tracker.record_event("tpl_2", "facebook", 300, 30, 6)
        stats = self.tracker.get_platform_stats("facebook")
        assert stats["total_impressions"] == 800
        assert stats["total_events"] == 2

    def test_top_performers(self):
        self.tracker.record_event("high", "facebook", 1000, 200, 50)
        self.tracker.record_event("low", "facebook", 1000, 10, 2)
        top = self.tracker.get_top_performers(platform="facebook")
        assert len(top) >= 2
        assert top[0]["template_id"] == "high"

    def test_update_template_from_events(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate()
        self.tracker.record_event(tpl.template_id, "facebook", 1000, 100, 50)
        self.tracker.update_template_from_events(tpl)
        assert tpl.total_impressions == 1000
        assert tpl.total_engagements == 100


# ══════════════════════════════════════════════════════════════════════
# VariationEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestVariationEngine:
    def setup_method(self):
        from layers.layer09_learning.modules.prompt_evolution.variation_engine import VariationEngine
        self.engine = VariationEngine()

    def test_generate_variations(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        base = PromptTemplate(topic="AI", platform="facebook", hook_type="question")
        variants = self.engine.generate_variations(base, count=3, strategy="mixed")
        assert len(variants) == 3
        assert all(v.parent_id == base.template_id for v in variants)
        assert all(v.generation == 2 for v in variants)

    def test_generate_hook_variations(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        base = PromptTemplate(topic="AI", hook_type="question")
        variants = self.engine.generate_variations(base, count=2, strategy="hook")
        assert len(variants) == 2
        assert all("hook" in v.metadata.get("variation_strategy", "") for v in variants)

    def test_generate_ab_test(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        champ = PromptTemplate(topic="AI")
        champ.record_use(impressions=10000, engagements=1000, clicks=500)
        challengers = self.engine.generate_ab_test(champ, count=2)
        assert len(challengers) == 2
        assert all("challenger" in ch.tags for ch in challengers)
        assert all(ch.metadata.get("ab_test") is True for ch in challengers)

    def test_generate_from_style(self):
        tpl = self.engine.generate_from_style("AI", "facebook", "facebook_educational")
        assert tpl.topic == "AI"
        assert tpl.platform == "facebook"
        assert len(tpl.hook_template) > 0
        assert len(tpl.cta_template) > 0

    def test_variation_count(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        base = PromptTemplate(topic="AI")
        self.engine.generate_variations(base, count=3)
        self.engine.generate_variations(base, count=2)
        assert self.engine.total_variations == 5

    def test_variations_have_unique_ids(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        base = PromptTemplate(topic="AI")
        variants = self.engine.generate_variations(base, count=5)
        ids = [v.template_id for v in variants]
        assert len(set(ids)) == 5


# ══════════════════════════════════════════════════════════════════════
# EvolutionEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestEvolutionEngine:
    def setup_method(self):
        from layers.layer09_learning.modules.prompt_evolution.evolution_engine import EvolutionEngine
        self.engine = EvolutionEngine()

    def test_evolve_empty_memory(self):
        """Evolution on empty memory should seed from style library."""
        cycle = self.engine.evolve(topic="AI", platform="facebook")
        assert cycle.templates_analyzed == 0
        assert cycle.challengers_generated >= 1
        assert len(cycle.insights) > 0

    def test_evolve_with_templates(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        for i in range(5):
            tpl = PromptTemplate(topic="AI", platform="facebook")
            tpl.record_use(impressions=1000, engagements=100, clicks=20)
            self.engine.get_memory().store(tpl)
        cycle = self.engine.evolve(topic="AI", platform="facebook")
        assert cycle.templates_analyzed == 5
        assert cycle.duration_ms > 0

    def test_get_best_template(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        good = PromptTemplate(topic="AI", platform="facebook")
        good.record_use(impressions=1000, engagements=200, clicks=50)
        self.engine.get_memory().store(good)
        best = self.engine.get_best_template("AI", "facebook")
        assert best is not None

    def test_record_performance(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI")
        self.engine.get_memory().store(tpl)
        self.engine.record_performance(tpl.template_id, "facebook", 1000, 100, 50)
        updated = self.engine.get_memory().get(tpl.template_id)
        assert updated.total_impressions == 1000

    def test_get_insights(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI", platform="facebook")
        tpl.record_use(impressions=1000, engagements=50, clicks=10)
        self.engine.get_memory().store(tpl)
        insights = self.engine.get_insights()
        assert insights["total_templates"] >= 1
        assert "avg_score" in insights

    def test_get_insights_empty(self):
        insights = self.engine.get_insights()
        assert insights["status"] == "no_data"

    def test_evolution_history(self):
        self.engine.evolve(topic="AI")
        self.engine.evolve(topic="Python")
        history = self.engine.get_memory()
        assert history.get_stats()["total_templates"] >= 2


# ══════════════════════════════════════════════════════════════════════
# Exceptions Tests
# ══════════════════════════════════════════════════════════════════════

class TestPromptEvolutionExceptions:
    def test_prompt_evolution_error(self):
        from layers.layer09_learning.modules.prompt_evolution.exceptions import PromptEvolutionError
        with pytest.raises(PromptEvolutionError):
            raise PromptEvolutionError("test error")

    def test_template_not_found(self):
        from layers.layer09_learning.modules.prompt_evolution.exceptions import TemplateNotFoundError
        with pytest.raises(TemplateNotFoundError):
            raise TemplateNotFoundError("not found")

    def test_style_not_found(self):
        from layers.layer09_learning.modules.prompt_evolution.exceptions import StyleNotFoundError
        with pytest.raises(StyleNotFoundError):
            raise StyleNotFoundError("style missing")

    def test_variation_limit(self):
        from layers.layer09_learning.modules.prompt_evolution.exceptions import VariationLimitError
        with pytest.raises(VariationLimitError):
            raise VariationLimitError("limit reached")

    def test_exception_hierarchy(self):
        from layers.layer09_learning.modules.prompt_evolution.exceptions import (
            PromptEvolutionError, TemplateNotFoundError, StyleNotFoundError,
        )
        assert issubclass(TemplateNotFoundError, PromptEvolutionError)
        assert issubclass(StyleNotFoundError, PromptEvolutionError)


# ══════════════════════════════════════════════════════════════════════
# CLI Commands Tests
# ══════════════════════════════════════════════════════════════════════

class TestCLICommands:
    def test_stats_command(self):
        """main.py --stats returns system statistics."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--stats"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert "version" in data
        assert "layers" in data
        assert "database" in data
        assert data["layers"] >= 20

    def test_analytics_command(self):
        """main.py --analytics returns analytics data."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--analytics"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert "analytics" in data
        assert "total_metrics" in data

    def test_history_command(self):
        """main.py --history returns content history."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--history", "--limit", "3"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert "history" in data
        assert "count" in data

    def test_history_platform_filter(self):
        """main.py --history --platform facebook filters by platform."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--history", "--platform", "facebook", "--limit", "5"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert data.get("platform_filter") == "facebook"
