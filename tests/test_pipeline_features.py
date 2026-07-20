"""Tests for v5.5.0 features: Pipeline Persistence, Gemini Image Provider, Real API Integration."""
from __future__ import annotations
import os
import sys
import time
import tempfile
import pytest


# ══════════════════════════════════════════════════════════════════════
# PipelinePersistence Tests
# ══════════════════════════════════════════════════════════════════════

class TestPipelinePersistence:
    def setup_method(self):
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "test.db")
        self.persist = PipelinePersistence(db_path=self._db_path)

    def teardown_method(self):
        self.persist.close()

    def test_save_content(self):
        content_id = self.persist.save_content(
            topic="AI Trends", platform="facebook", content="Test content here",
            image_prompt="An AI brain", quality_score=8.5, status="generated",
        )
        assert content_id > 0

    def test_save_analytics(self):
        row_id = self.persist.save_analytics("quality_score", 8.5, source="test")
        assert row_id > 0

    def test_save_learning(self):
        row_id = self.persist.save_learning(
            lesson_type="pipeline_execution",
            input_summary="Topic: AI", output_summary="Great content",
            feedback_score=0.85,
        )
        assert row_id > 0

    def test_save_log(self):
        row_id = self.persist.save_log("INFO", "test_module", "Test log message")
        assert row_id > 0

    def test_save_config(self):
        self.persist.save_config("test_key", "test_value", "test_category")
        result = self.persist._db.query_one(
            "SELECT value FROM agent_config WHERE key = 'test_key'"
        )
        assert result is not None
        assert result["value"] == "test_value"

    def test_update_config(self):
        self.persist.save_config("k", "v1")
        self.persist.save_config("k", "v2")
        result = self.persist._db.query_one("SELECT value FROM agent_config WHERE key = 'k'")
        assert result["value"] == "v2"

    def test_save_pipeline_run(self):
        response_dict = {
            "topic": "Test Topic",
            "platform": "twitter",
            "content_length": 250,
            "quality_score": 7.5,
            "steps_completed": 9,
        }
        content_id = self.persist.save_pipeline_run(response_dict)
        assert content_id > 0

    def test_get_content_history(self):
        self.persist.save_content(topic="t1", platform="facebook", content="c1")
        self.persist.save_content(topic="t2", platform="twitter", content="c2")
        history = self.persist.get_content_history()
        assert len(history) == 2

    def test_get_content_history_filtered(self):
        self.persist.save_content(topic="t1", platform="facebook", content="c1")
        self.persist.save_content(topic="t2", platform="twitter", content="c2")
        fb_history = self.persist.get_content_history(platform="facebook")
        assert len(fb_history) == 1
        assert fb_history[0]["platform"] == "facebook"

    def test_get_analytics_summary(self):
        self.persist.save_analytics("score", 8.0, source="test")
        self.persist.save_analytics("score", 9.0, source="test")
        summary = self.persist.get_analytics_summary()
        assert "score" in summary
        assert summary["score"]["count"] == 2

    def test_get_learning_history(self):
        self.persist.save_learning("type1", "input1", "output1", 0.9)
        history = self.persist.get_learning_history()
        assert len(history) >= 1

    def test_get_db_stats(self):
        stats = self.persist.get_db_stats()
        assert "tables" in stats
        assert "total_rows" in stats


# ══════════════════════════════════════════════════════════════════════
# GeminiImageProvider Tests
# ══════════════════════════════════════════════════════════════════════

class TestGeminiImageProvider:
    def setup_method(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        self.provider = GeminiImageProvider(api_key="test_key_for_testing")

    def test_generate_without_api(self):
        """Without real API key, should return enhanced prompt."""
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        result = prov.generate("A sunset over mountains", size="1024x1024")
        assert result is not None
        assert result.provider == "gemini_image_prompt"
        assert len(result.revised_prompt) > 0
        assert result.metadata.get("enhanced") is True

    def test_enhanced_prompt_contains_details(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        result = prov.generate("A cat playing piano", style="cartoon")
        assert "cartoon" in result.revised_prompt.lower()
        assert "cat" in result.revised_prompt.lower()

    def test_generate_batch(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        results = prov.generate_batch(["prompt1", "prompt2"], size="1024x1024")
        assert len(results) == 2
        assert all(r.revised_prompt for r in results)

    def test_is_configured(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="real_key")
        assert prov.is_configured() is True
        prov2 = GeminiImageProvider(api_key="")
        assert prov2.is_configured() is False

    def test_get_stats(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        prov.generate("test")
        stats = prov.get_stats()
        assert stats["total_calls"] == 1
        assert stats["provider"] == "gemini_image"

    def test_history_tracking(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        prov.generate("prompt1")
        prov.generate("prompt2")
        history = prov.get_history()
        assert len(history) == 2

    def test_size_parsing(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        w, h = prov._parse_size("1920x1080")
        assert w == 1920
        assert h == 1080

    def test_enhanced_prompt_landscape(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        result = prov.generate("test", size="1920x1080")
        assert "landscape" in result.revised_prompt.lower()

    def test_enhanced_prompt_portrait(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        result = prov.generate("test", size="1080x1920")
        assert "portrait" in result.revised_prompt.lower()

    def test_generate_with_reference(self):
        from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
        prov = GeminiImageProvider(api_key="")
        result = prov.generate_with_reference("A mountain", reference_url="http://example.com/ref.jpg")
        assert "reference" in result.revised_prompt.lower()


# ══════════════════════════════════════════════════════════════════════
# PipelineWiring Integration Tests
# ══════════════════════════════════════════════════════════════════════

class TestPipelineWiringIntegration:
    def test_pipeline_with_persistence(self):
        """Full pipeline run should persist to database."""
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest,
        )
        pipe = PipelineWiring()
        req = ContentRequest(
            topic="Integration Test Topic",
            platform="linkedin",
            tone="professional",
            style="educational",
            include_image=True,
        )
        response = pipe.execute(req)
        assert response is not None
        assert len(response.steps) == 9
        assert response.text is not None

    def test_pipeline_persistence_saves_data(self):
        """Pipeline run should create database entries."""
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest,
        )
        pipe = PipelineWiring()
        req = ContentRequest(topic="DB Test", platform="twitter", include_image=True)
        response = pipe.execute(req)
        # Check that persistence worked by querying the database
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        persist = PipelinePersistence()
        history = persist.get_content_history(platform="twitter")
        persist.close()
        assert len(history) >= 1

    def test_pipeline_image_generation(self):
        """Pipeline should attempt image generation via Gemini."""
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest,
        )
        pipe = PipelineWiring()
        req = ContentRequest(topic="Image Test", platform="instagram", include_image=True)
        response = pipe.execute(req)
        assert response.image_prompt is not None
        assert len(response.image_prompt) > 0

    def test_pipeline_without_image(self):
        """Pipeline with include_image=False should skip image step."""
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest,
        )
        pipe = PipelineWiring()
        req = ContentRequest(topic="No Image", platform="facebook", include_image=False)
        response = pipe.execute(req)
        img_step = next((s for s in response.steps if s.layer == "L5-Image"), None)
        assert img_step is not None
        # When include_image=False, step returns data with skipped=True but status is success (no exception)
        assert img_step.data.get("skipped") is True

    def test_pipeline_multiple_runs(self):
        """Multiple pipeline runs should each create database entries."""
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest,
        )
        pipe = PipelineWiring()
        for topic in ["Run 1", "Run 2", "Run 3"]:
            req = ContentRequest(topic=topic, platform="facebook", include_image=False)
            pipe.execute(req)

        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        persist = PipelinePersistence()
        history = persist.get_content_history(platform="facebook")
        persist.close()
        assert len(history) >= 3
