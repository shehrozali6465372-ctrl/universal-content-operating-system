"""Tests for v5.8.0 production features: Docker, Facebook Publisher, Template Ranking."""
from __future__ import annotations
import os
import tempfile
import pytest


# ══════════════════════════════════════════════════════════════════════
# Docker Tests
# ══════════════════════════════════════════════════════════════════════

class TestDockerDeployment:
    def test_dockerfile_exists(self):
        assert os.path.exists("Dockerfile")

    def test_dockerfile_has_healthcheck(self):
        with open("Dockerfile") as f:
            content = f.read()
        assert "HEALTHCHECK" in content
        assert "python:3.12-slim" in content

    def test_dockerfile_has_non_root_user(self):
        with open("Dockerfile") as f:
            content = f.read()
        assert "useradd" in content or "USER" in content

    def test_docker_compose_exists(self):
        assert os.path.exists("docker-compose.yml")

    def test_docker_compose_has_services(self):
        with open("docker-compose.yml") as f:
            content = f.read()
        assert "aios:" in content
        assert "aios-worker:" in content

    def test_docker_compose_has_volumes(self):
        with open("docker-compose.yml") as f:
            content = f.read()
        assert "aios-data:" in content

    def test_docker_compose_has_healthcheck(self):
        with open("docker-compose.yml") as f:
            content = f.read()
        assert "healthcheck:" in content

    def test_dockerignore_exists(self):
        assert os.path.exists(".dockerignore")

    def test_dockerignore_excludes_tests(self):
        with open(".dockerignore") as f:
            content = f.read()
        assert "tests/" in content

    def test_dockerignore_excludes_git(self):
        with open(".dockerignore") as f:
            content = f.read()
        assert ".git" in content

    def test_docker_config_class(self):
        from layers.layer21_deployment.modules.docker_engine.docker_engine import DockerConfig
        config = DockerConfig(image="aios", tag="v5.8.0")
        assert config.image == "aios"
        assert config.tag == "v5.8.0"
        d = config.to_dict()
        assert "aios:v5.8.0" in d["image"]


# ══════════════════════════════════════════════════════════════════════
# Facebook Publisher Tests
# ══════════════════════════════════════════════════════════════════════

class TestFacebookPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
        self.publisher = FacebookPublisher()

    def test_platform_name(self):
        assert self.publisher.get_platform_name() == "facebook"

    def test_capabilities(self):
        caps = self.publisher.get_capabilities()
        assert caps.supports_images is True
        assert caps.supports_video is True
        assert caps.supports_scheduled is True
        assert caps.supports_analytics is True
        assert caps.max_length > 10000

    def test_validate_valid_content(self):
        assert self.publisher.validate("Hello world!") is True

    def test_validate_empty_content(self):
        assert self.publisher.validate("") is False

    def test_validate_whitespace_only(self):
        assert self.publisher.validate("   ") is False

    def test_authenticate_without_credentials(self):
        result = self.publisher.authenticate({})
        # Should fail without real credentials
        assert result is False

    def test_publish_without_auth(self):
        result = self.publisher.publish("Test post")
        assert result.success is False
        assert "Not authenticated" in result.error_message

    def test_publish_result_structure(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import PublishResult
        result = PublishResult(success=True, platform="facebook")
        d = result.to_dict()
        assert d["success"] is True
        assert d["platform"] == "facebook"

    def test_get_stats(self):
        stats = self.publisher.get_stats()
        assert stats["platform"] == "facebook"
        assert "authenticated" in stats
        assert "total_requests" in stats

    def test_edit_without_auth(self):
        result = self.publisher.edit("post_123", "Updated content")
        assert result.success is False

    def test_delete_without_auth(self):
        result = self.publisher.delete("post_123")
        assert result is False

    def test_get_post_without_auth(self):
        result = self.publisher.get_post("post_123")
        assert result is None

    def test_get_status_without_auth(self):
        status = self.publisher.get_status("post_123")
        assert status == "unknown"

    def test_schedule_without_auth(self):
        import time
        result = self.publisher.schedule("Test", time.time() + 3600)
        assert result.success is False

    def test_platform_capabilities_to_dict(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import PlatformCapabilities
        caps = PlatformCapabilities()
        caps.supports_images = True
        caps.max_length = 63206
        d = caps.to_dict()
        assert d["supports_images"] is True
        assert d["max_length"] == 63206


# ══════════════════════════════════════════════════════════════════════
# Template Ranking Tests
# ══════════════════════════════════════════════════════════════════════

class TestTemplateRanker:
    def setup_method(self):
        from layers.layer09_learning.modules.prompt_evolution.template_ranker import TemplateRanker
        self.ranker = TemplateRanker()

    def test_rank_template(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        tpl = PromptTemplate(topic="AI", platform="facebook")
        score = self.ranker.rank_template(tpl, impressions=1000, engagements=100, clicks=20)
        assert score > 0
        assert tpl.total_impressions == 1000

    def test_rank_batch(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        templates = [
            PromptTemplate(topic="AI", platform="facebook"),
            PromptTemplate(topic="Python", platform="facebook"),
        ]
        perf_data = [
            {"impressions": 1000, "engagements": 100, "clicks": 20},
            {"impressions": 500, "engagements": 50, "clicks": 10},
        ]
        results = self.ranker.rank_batch(templates, perf_data)
        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]

    def test_get_best_template(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        good = PromptTemplate(topic="AI", platform="facebook")
        good.record_use(impressions=1000, engagements=200, clicks=50)
        self.ranker.get_memory().store(good)

        best = self.ranker.get_best_template(platform="facebook", topic="AI")
        assert best is not None
        assert best.topic == "AI"

    def test_get_rankings(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        for i in range(5):
            tpl = PromptTemplate(topic=f"topic_{i}", platform="facebook")
            tpl.record_use(impressions=1000, engagements=i * 50, clicks=i * 10)
            self.ranker.get_memory().store(tpl)

        rankings = self.ranker.get_rankings(platform="facebook")
        assert len(rankings) == 5
        assert rankings[0]["score"] >= rankings[-1]["score"]

    def test_get_hook_performance(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        for hook in ["question", "statistic", "story"]:
            tpl = PromptTemplate(topic="AI", platform="facebook", hook_type=hook)
            tpl.record_use(impressions=1000, engagements=100, clicks=20)
            self.ranker.get_memory().store(tpl)

        hook_perf = self.ranker.get_hook_performance(platform="facebook")
        assert len(hook_perf) >= 3
        assert all("avg_score" in v for v in hook_perf.values())

    def test_get_cta_performance(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        for cta in ["ask_question", "share_opinion", "save_post"]:
            tpl = PromptTemplate(topic="AI", platform="facebook", cta_type=cta)
            tpl.record_use(impressions=1000, engagements=100, clicks=20)
            self.ranker.get_memory().store(tpl)

        cta_perf = self.ranker.get_cta_performance(platform="facebook")
        assert len(cta_perf) >= 3

    def test_ranking_order_is_descending(self):
        from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
        for i in range(3):
            tpl = PromptTemplate(topic=f"t{i}", platform="facebook")
            tpl.record_use(impressions=1000, engagements=(3 - i) * 50, clicks=(3 - i) * 10)
            self.ranker.get_memory().store(tpl)

        rankings = self.ranker.get_rankings()
        scores = [r["score"] for r in rankings]
        assert scores == sorted(scores, reverse=True)
