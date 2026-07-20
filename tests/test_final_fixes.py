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
        assert data["version"] == "5.8.0"
        assert data["total_layers"] == 22

    def test_boot_command(self):
        """main.py should boot all layers without errors."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "Boot complete: 20/20" in result.stdout

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
        assert resp.text is not None
        assert len(resp.text) > 0
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
