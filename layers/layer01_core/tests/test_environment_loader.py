"""
Tests for Environment Loader Module
Layer 1: Core System — Module 3

Run: python -m pytest layers/layer01_core/tests/test_environment_loader.py -v
"""

import os
import time
import pytest
import json
from layers.layer01_core.modules.environment_loader import EnvironmentLoader
from layers.layer01_core.modules.env_profiles import (
    get_profile, get_available_profiles,
)
from layers.layer01_core.modules.exceptions import InvalidConfig


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test."""
    saved = {}
    for key in list(os.environ.keys()):
        if key.startswith("AGENT_") or key in (
            "OPENAI_API_KEY", "FACEBOOK_PAGE_ID", "FACEBOOK_ACCESS_TOKEN"
        ):
            saved[key] = os.environ.pop(key)
    yield
    os.environ.update(saved)


@pytest.fixture
def loader(tmp_path):
    """Create a fresh EnvironmentLoader."""
    (tmp_path / ".env").write_text(
        'OPENAI_API_KEY="sk-test-12345"\n'
        'FACEBOOK_PAGE_ID=12345\n'
        'FACEBOOK_ACCESS_TOKEN=fb_token_xyz\n'
    )
    return EnvironmentLoader(project_root=str(tmp_path), audit_log_path=str(tmp_path / "logs/audit.log"))


# ── Test 1: Profiles ───────────────────────

class TestProfiles:
    def test_get_dev_profile(self):
        p = get_profile("dev")
        assert p is not None
        assert p.name == "development"

    def test_get_prod_profile(self):
        p = get_profile("prod")
        assert p is not None
        assert p.name == "production"

    def test_get_unknown_profile(self):
        assert get_profile("staging") is None

    def test_available_profiles(self):
        profiles = get_available_profiles()
        assert "development" in profiles
        assert "testing" in profiles
        assert "production" in profiles


# ── Test 2: Loading ────────────────────────

class TestLoading:
    def test_load_development(self, loader):
        loader.load(profile="dev")
        assert loader.is_loaded is True
        assert loader.current_profile == "development"

    def test_load_test(self, loader):
        loader.load(profile="test")
        assert loader.current_profile == "testing"

    def test_load_prod(self, loader):
        loader.load(profile="prod")
        assert loader.current_profile == "production"

    def test_load_unknown_raises(self, loader):
        with pytest.raises(ValueError, match="Unknown environment profile"):
            loader.load(profile="staging")

    def test_env_file_values_loaded(self, loader):
        loader.load(profile="dev")
        assert loader.get("OPENAI_API_KEY") == "sk-test-12345"
        assert loader.get("FACEBOOK_PAGE_ID") == "12345"

    def test_profile_defaults_applied(self, loader):
        loader.load(profile="dev")
        assert loader.get("LOG_LEVEL") == "DEBUG"
        assert loader.get("AI_MODEL") == "gpt-3.5-turbo"
        assert loader.get("MAX_POSTS_PER_DAY") == "2"

    def test_all_returns_dict(self, loader):
        loader.load(profile="dev")
        result = loader.all()
        assert isinstance(result, dict)
        assert "OPENAI_API_KEY" in result


# ── Test 3: Override Priority ───────────────

class TestOverridePriority:
    def test_system_env_overrides_profile(self, loader):
        os.environ["OPENAI_API_KEY"] = "sk-system-key"
        loader.load(profile="dev")
        assert loader.get("OPENAI_API_KEY") == "sk-system-key"
        del os.environ["OPENAI_API_KEY"]

    def test_agent_prefix_overrides_all(self, loader):
        os.environ["AGENT_LOG_LEVEL"] = "CRITICAL"
        loader.load(profile="dev")
        assert loader.get("LOG_LEVEL") == "CRITICAL"
        del os.environ["AGENT_LOG_LEVEL"]


# ── Test 4: Access ─────────────────────────

class TestAccess:
    def test_get_with_default(self, loader):
        loader.load(profile="dev")
        assert loader.get("DOES_NOT_EXIST", "fallback") == "fallback"

    def test_set_runtime(self, loader):
        loader.load(profile="dev")
        loader.set("CUSTOM_VAR", "hello")
        assert loader.get("CUSTOM_VAR") == "hello"

    def test_has(self, loader):
        loader.load(profile="dev")
        assert loader.has("OPENAI_API_KEY") is True
        assert loader.has("NONEXISTENT") is False


# ── Test 5: Validation ─────────────────────

class TestValidation:
    def test_validate_passes_with_all_vars(self, loader):
        loader.load(profile="dev")
        errors = loader.validate()
        assert errors == []

    def test_validate_fails_missing_required(self, tmp_path):
        # Create .env without required keys for prod
        (tmp_path / ".env").write_text("LOG_LEVEL=DEBUG\n")
        loader = EnvironmentLoader(project_root=str(tmp_path))
        loader.load(profile="prod")
        errors = loader.validate()
        assert len(errors) >= 1
        assert any("OPENAI_API_KEY" in e for e in errors)

    def test_validate_strict_raises(self, tmp_path):
        (tmp_path / ".env").write_text("LOG_LEVEL=DEBUG\n")
        loader = EnvironmentLoader(project_root=str(tmp_path))
        loader.load(profile="prod")
        with pytest.raises(InvalidConfig):
            loader.validate_strict()


# ── Test 6: Auto-Reload ────────────────────

class TestAutoReload:
    def test_reload_detects_file_change(self, loader):
        env_path = loader._project_root / ".env"
        env_path.write_text('OPENAI_API_KEY="sk-old"\n')
        loader.load(profile="dev")

        time.sleep(0.1)
        env_path.write_text('OPENAI_API_KEY="sk-new"\n')
        reloaded = loader.reload()
        assert reloaded is True
        assert loader.get("OPENAI_API_KEY") == "sk-new"

    def test_reload_no_change_returns_false(self, loader):
        loader.load(profile="dev")
        reloaded = loader.reload()
        assert reloaded is False


# ── Test 7: Health Check ───────────────────

class TestHealthCheck:
    def test_health_check_pass(self, loader):
        loader.load(profile="dev")
        report = loader.health_check()
        assert report["overall"] in ("PASS", "WARN")
        assert "profile" in report["checks"]
        assert "required_vars" in report["checks"]

    def test_health_check_without_load(self, tmp_path):
        loader = EnvironmentLoader(project_root=str(tmp_path))
        report = loader.health_check()
        assert report["overall"] == "FAIL"
        assert report["checks"]["profile"]["status"] == "FAIL"


# ── Test 8: Snapshot ───────────────────────

class TestSnapshot:
    def test_snapshot_hides_secrets(self, loader):
        loader.load(profile="dev")
        result = loader.snapshot(str(loader._project_root / "data/snap.json"))
        assert result["profile"] == "development"
        # Check secrets are hidden
        assert loader._project_root / "data" / "snap.json"
        content = json.loads((loader._project_root / "data" / "snap.json").read_text())
        assert content["variables"]["OPENAI_API_KEY"] == "***SECRET***"
        assert content["variables"]["FACEBOOK_ACCESS_TOKEN"] == "***SECRET***"

    def test_snapshot_shows_non_secrets(self, loader):
        loader.load(profile="dev")
        result = loader.snapshot(str(loader._project_root / "data/snap.json"))
        assert result["variables"]["LOG_LEVEL"] == "DEBUG"


# ── Test 9: Reset ──────────────────────────

class TestReset:
    def test_reset_clears_state(self, loader):
        loader.load(profile="dev")
        assert loader.is_loaded is True
        loader.reset()
        assert loader.is_loaded is False
        assert loader.current_profile is None
        assert loader.all() == {}
