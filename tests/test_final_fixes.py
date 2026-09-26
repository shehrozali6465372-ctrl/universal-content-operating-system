"""Tests for final fixes — main.py, PipelineWiring, README accuracy."""
from __future__ import annotations
import os
import time
import pytest


class TestMainPy:
    def test_status_command(self):
        """main.py --status should return 22 layers."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--status"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert data["version"] == "6.0.0"
        assert data["total_layers"] == 23

    def test_boot_command(self):
        """main.py should boot all layers without errors."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "Boot complete:" in result.stdout

    def test_generate_no_keys(self):
        """main.py --generate should work even without API keys (simulated)."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--generate", "AI trends"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "topic" in result.stdout or "content" in result.stdout


class TestPipelineWiring:
    def setup_method(self):
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest
        )
        self.PipelineWiring = PipelineWiring
        self.ContentRequest = ContentRequest

    def test_pipeline_execute(self):
        """Full pipeline: request → text → response."""
        pw = self.PipelineWiring()
        req = self.ContentRequest("artificial intelligence", platform="instagram")
        resp = pw.execute(req)
        assert resp is not None
        assert resp.stats["execution_time_ms"] >= 0

    def test_pipeline_with_image(self):
        """Pipeline with image prompt generation."""
        pw = self.PipelineWiring()
        req = self.ContentRequest("climate change", include_image=True)
        resp = pw.execute(req)
        assert resp.text is not None

    def test_pipeline_status(self):
        pw = self.PipelineWiring()
        status = pw.status()
        assert "api_keys_configured" in status
        assert "api_keys_configured" in status

    def test_pipeline_different_platforms(self):
        """Same topic, different platforms."""
        pw = self.PipelineWiring()
        for platform in ["facebook", "instagram", "linkedin", "twitter"]:
            req = self.ContentRequest("AI trends", platform=platform)
            resp = pw.execute(req)
            assert resp.text is not None

    def test_pipeline_quality_score(self):
        pw = self.PipelineWiring()
        req = self.ContentRequest("testing")
        resp = pw.execute(req)
        assert resp.quality_score >= 0

    def test_l3_intelligence_wires_keyword_analysis(self):
        pw = self.PipelineWiring()
        req = self.ContentRequest("AI tools improve productivity", platform="facebook")
        resp = pw.execute(req)
        step = next(s for s in resp.steps if s.layer == "L3-Intelligence")
        assert step.status == "success"
        assert step.data["keywords"]
        assert step.data["entities"] is not None
        assert step.data["intent"]

    def test_offline_draft_cannot_publish(self):
        pw = self.PipelineWiring()
        req = self.ContentRequest("offline production guard", platform="facebook")
        resp = pw.execute(req)
        assert not (resp.publish_result and resp.publish_result.get("success"))
        publish_step = next((s for s in resp.steps if s.layer == "L7-Publish"), None)
        if pw.status()["api_keys_configured"] == 0:
            # A required upstream image failure can stop the graph before L7;
            # either way no publish result may report success.
            if publish_step is not None:
                assert publish_step.status == "error"
                assert "offline-draft" in (publish_step.error or "") or "image" in (publish_step.error or "").lower()

    def test_pipeline_content_request_to_dict(self):
        req = self.ContentRequest("test", platform="youtube", tone="casual")
        d = req.to_dict()
        assert d["platform"] == "youtube"
        assert d["tone"] == "casual"


class TestRequirementsTxt:
    def test_requirements_exist(self):
        with open("requirements.txt") as f:
            content = f.read()
        assert "pytest" in content
        assert "ruff" in content

    def test_no_broken_imports(self):
        """requirements.txt should not list unused heavy deps."""
        with open("requirements.txt") as f:
            content = f.read()
        # These should be commented out or removed
        # (they're not actually used in the codebase)
        for line in content.split("\n"):
            if line.startswith("facebook-sdk") or line.startswith("langchain"):
                assert line.startswith("#"), f"Unused dep not commented: {line}"


def test_quality_hard_gates_reject_bad_content():
    from layers.layer06_quality.modules.content_quality_analyzer.quality_analyzer import ContentQualityAnalyzer
    analyzer = ContentQualityAnalyzer()
    for text in ("", "Hello", "lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                 "As an AI language model, I cannot help with this request.",
                 "Get 500% guaranteed returns and send your bank password now."):
        report = analyzer.analyze(text, platform="facebook")
        assert report.overall_score == 0.0
        assert report.pass_recommendation == "REVISION REQUIRED"
        assert report.metadata["hard_gate_failures"]


def test_quality_platform_and_score_scale_are_real():
    from layers.layer06_quality.modules.content_quality_analyzer.quality_analyzer import ContentQualityAnalyzer
    report = ContentQualityAnalyzer().analyze(
        "Practical productivity tips can help teams plan focused work, reduce context switching, and review results each week.",
        platform="linkedin",
    )
    assert report.metadata["platform"] == "linkedin"
    assert 0.0 <= report.overall_score <= 1.0


def test_publisher_manager_skips_second_repetition_reservation(monkeypatch):
    from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
    from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
    manager = PublisherManager()
    monkeypatch.setattr(manager, "_get_publisher", lambda platform: None)
    monkeypatch.setattr(manager, "_account_repetition_guard",
                        lambda account_id: (_ for _ in ()).throw(AssertionError("second gate")))
    request = PublishRequest(platform="facebook", content="already reserved by production pipeline")
    request.metadata.update({"account_id": "acct", "repetition_reserved_by_pipeline": True})
    result = manager.publish(request)
    assert result is not None
    assert "second gate" not in (result.error_message or "")


def test_l12_select_key_returns_registered_secret():
    from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
    km = KeyManager()
    km.register_key("k1", "secret-key-123456")
    assert km.select_key() == "secret-key-123456"


def test_facebook_attached_media_is_json():
    import json
    from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
    from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import PublishResult
    publisher = FacebookPublisher()
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(publisher, "upload_image",
                            lambda path, caption="": PublishResult(platform="facebook", success=True, post_id="123"))
        captured = {}
        monkeypatch.setattr(publisher, "_post", lambda path, payload: (captured.update(payload) or {"id": "post"}))
        publisher._publish_with_media("hello", ["image.jpg"])
        assert captured["attached_media"] == [{"media_fbid": "123"}]
    finally:
        monkeypatch.undo()


def test_instagram_waits_for_finished_container(monkeypatch):
    from layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher import InstagramPublisher
    publisher = InstagramPublisher()
    states = iter([{"status_code": "IN_PROGRESS"}, {"status_code": "FINISHED"}])
    monkeypatch.setattr(publisher, "_api_get", lambda endpoint, params=None: next(states))
    monkeypatch.setattr("time.sleep", lambda _: None)
    publisher._wait_for_container("container", timeout=1, interval=0)


def test_affiliate_program_requires_explicit_verification_before_link():
    from layers.layer10_monetization.modules.affiliate_engine.affiliate_manager import AffiliateManager
    manager = AffiliateManager()
    program = manager.get_program("amazon")
    assert program is not None
    assert program.status == "unconfigured"
    with pytest.raises(ValueError):
        manager.add_link(program.id, "https://example.com/product", "https://example.com/affiliate")
    manager.verify_program("amazon", "operator-verification-001")
    link = manager.add_link(program.id, "https://example.com/product", "https://example.com/affiliate")
    assert link.status == "active"


def test_forecast_requires_real_history_and_exposes_provenance():
    from layers.layer19_analytics_engine.modules.bi_platform.revenue_forecasting import RevenueForecasting
    model = RevenueForecasting()
    with pytest.raises(ValueError):
        model.forecast_30_days()
    model.add_historical("2026-01-01", 100.0, 20.0)
    model.add_historical("2026-01-02", 120.0, 24.0)
    point = model.forecast_30_days()[0]
    assert point.model == "ordinary_least_squares_linear_trend"
    assert point.provenance["observation_count"] == 2


def test_learning_feedback_requires_account_platform_niche_scope():
    from layers.layer09_learning.modules.self_improvement.self_improvement_manager import SelfImprovementManager
    manager = SelfImprovementManager()
    result = manager.apply_analytics_feedback({
        "available": True,
        "diagnosis": ["low_click_through_rate"],
    })
    assert result["updated"] is False
    assert result["reason"] == "scope_required"


def test_atoz_replay_is_fail_closed_for_inflight_request(monkeypatch, tmp_path):
    import layers.layer23_website_manager.integration.atoz_bridge as bridge
    monkeypatch.setattr(bridge, "_INBOX_DB", tmp_path / "jobs.sqlite3")
    request_id = str(__import__("uuid").uuid4())
    bridge._claim_request(request_id, "hash")
    with pytest.raises(RuntimeError, match="requires reconciliation"):
        bridge._claim_request(request_id, "hash")
