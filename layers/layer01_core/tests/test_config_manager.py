"""
Tests for Config Manager Module
Layer 1: Core System — Module 1

Run: python -m pytest layers/layer01_core/tests/test_config_manager.py -v
"""

import os
import pytest
from layers.layer01_core.modules.config_manager import ConfigManager
from layers.layer01_core.modules.exceptions import (
    ConfigNotFound,
    InvalidConfig,
    MissingAPIKey,
    SchemaError,
)


@pytest.fixture(autouse=True)
def reset():
    """Reset singleton before each test."""
    ConfigManager.reset()
    yield
    ConfigManager.reset()


# ── Test 1: Singleton ──────────────────────

class TestSingleton:
    def test_returns_same_instance(self):
        c1 = ConfigManager()
        c2 = ConfigManager()
        assert c1 is c2

    def test_singleton_not_reinitialized(self):
        c1 = ConfigManager()
        c1.set("test_key", "test_val")
        c2 = ConfigManager()
        assert c2.get("test_key") == "test_val"


# ── Test 2: Load ───────────────────────────

class TestLoading:
    def test_load_yaml(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text(
            "database:\n  host: localhost\n  port: 5432\n"
        )
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432

    def test_load_env(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test123"\nFACEBOOK_PAGE_ID=12345\n'
        )
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("OPENAI_API_KEY") == "sk-test123"
        assert config.get("FACEBOOK_PAGE_ID") == "12345"

    def test_env_overrides_yaml(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text(
            "app:\n  name: default\n"
        )
        (tmp_path / ".env").write_text("app.name=overridden\n")
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("app.name") == "overridden"

    def test_agent_prefix_env_override(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text(
            "LOG_LEVEL: INFO\n"
        )
        os.environ["AGENT_LOG_LEVEL"] = "DEBUG"
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("LOG_LEVEL") == "DEBUG"
        del os.environ["AGENT_LOG_LEVEL"]


# ── Test 3: Optional Defaults ───────────────

class TestDefaults:
    def test_defaults_applied_when_missing(self, tmp_path):
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("LOG_LEVEL") == "INFO"
        assert config.get("DATABASE_PATH") == "data/agent.db"
        assert config.get("DEBUG") is False
        assert config.get("MAX_POSTS_PER_DAY") == 5
        assert config.get("AI_MODEL") == "gpt-4"


# ── Test 4: Get / Set / Has ────────────────

class TestGetSetHas:
    def test_get_with_default(self, tmp_path):
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("missing", "fallback") == "fallback"

    def test_set_and_get(self, tmp_path):
        config = ConfigManager(project_root=tmp_path)
        config.load()
        config.set("CUSTOM", 42)
        assert config.get("CUSTOM") == 42

    def test_has(self, tmp_path):
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.has("LOG_LEVEL") is True
        assert config.has("DOES_NOT_EXIST") is False


# ── Test 5: Validation ─────────────────────

class TestValidation:
    def test_validate_passes_with_valid_config(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test123"\n'
            'FACEBOOK_PAGE_ID=12345\n'
            'FACEBOOK_ACCESS_TOKEN=abc_token\n'
            'LOG_LEVEL=INFO\n'
        )
        config = ConfigManager(project_root=tmp_path)
        config.load()
        errors = config.validate()
        assert errors == []

    def test_validate_fails_missing_required(self, tmp_path):
        config = ConfigManager(project_root=tmp_path)
        config.load()
        errors = config.validate()
        assert len(errors) >= 3
        assert any("OPENAI_API_KEY" in e for e in errors)
        assert any("FACEBOOK_PAGE_ID" in e for e in errors)

    def test_validate_strict_raises(self, tmp_path):
        config = ConfigManager(project_root=tmp_path)
        config.load()
        with pytest.raises(SchemaError):
            config.validate_strict()

    def test_validate_catches_invalid_log_level(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test123"\n'
            'FACEBOOK_PAGE_ID=12345\n'
            'FACEBOOK_ACCESS_TOKEN=abc\n'
            'LOG_LEVEL=MEGA_VERBOSE\n'
        )
        config = ConfigManager(project_root=tmp_path)
        config.load()
        errors = config.validate()
        assert any("LOG_LEVEL" in e for e in errors)


# ── Test 6: Save ───────────────────────────

class TestSave:
    def test_save_creates_json_file(self, tmp_path):
        (tmp_path / "config").mkdir()
        config = ConfigManager(project_root=tmp_path)
        config.load()
        config.set("MY_KEY", "my_value")
        config.save("config/agent_config.json")

        assert (tmp_path / "config" / "agent_config.json").exists()
        import json
        saved = json.loads((tmp_path / "config" / "agent_config.json").read_text())
        assert saved["MY_KEY"] == "my_value"
