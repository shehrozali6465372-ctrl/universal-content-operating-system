"""
Tests for Config Manager Module
Layer 1: Core System — Module 1
"""

import os
import json
import pytest
from layers.layer01_core.modules.config_manager import ConfigManager, CONFIG_VERSION
from layers.layer01_core.modules.exceptions import InvalidConfig, SchemaError


@pytest.fixture(autouse=True)
def reset():
    ConfigManager.reset()
    yield
    ConfigManager.reset()


class TestSingleton:
    def test_returns_same_instance(self):
        assert ConfigManager() is ConfigManager()

    def test_singleton_not_reinitialized(self):
        c1 = ConfigManager()
        c1.set("CUSTOM_KEY", "value1")
        assert ConfigManager().get("CUSTOM_KEY") == "value1"

    def test_singleton_isolated_by_project_root(self, tmp_path):
        other = tmp_path / "other"
        other.mkdir()
        first = ConfigManager(project_root=tmp_path)
        second = ConfigManager(project_root=other)
        first.set("SCOPED_KEY", "one")
        second.set("SCOPED_KEY", "two")
        assert first.get("SCOPED_KEY") == "one"
        assert second.get("SCOPED_KEY") == "two"


class TestLoading:
    def test_load_yaml(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text(
            "database:\n  host: localhost\n  port: 5432\n"
        )
        config = ConfigManager(project_root=tmp_path).load()
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432

    def test_load_env(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test123"\nFACEBOOK_PAGE_ID=12345\n'
        )
        config = ConfigManager(project_root=tmp_path).load()
        assert config.get("OPENAI_API_KEY") == "sk-test123"
        assert config.get("FACEBOOK_PAGE_ID") == "12345"

    def test_env_overrides_yaml(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text("app:\n  name: default\n")
        (tmp_path / ".env").write_text("app.name=overridden\n")
        config = ConfigManager(project_root=tmp_path).load()
        assert config.get("app.name") == "overridden"

    def test_agent_prefix_env_override(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text("LOG_LEVEL: INFO\n")
        os.environ["AGENT_LOG_LEVEL"] = "DEBUG"
        try:
            config = ConfigManager(project_root=tmp_path).load()
            assert config.get("LOG_LEVEL") == "DEBUG"
        finally:
            os.environ.pop("AGENT_LOG_LEVEL", None)


class TestDefaults:
    def test_defaults_applied(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        assert config.get("LOG_LEVEL") == "INFO"
        assert config.get("DATABASE_PATH") == "data/agent.db"
        assert config.get("DEBUG") is False
        assert config.get("MAX_POSTS_PER_DAY") == 5
        assert config.get("AI_MODEL") == "gpt-4"
        assert config.get("AI_TEMPERATURE") == 0.7


class TestGetSetHas:
    def test_get_with_default(self, tmp_path):
        assert ConfigManager(project_root=tmp_path).load().get("missing", "fallback") == "fallback"

    def test_set_and_get(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        config.set("CUSTOM", 42)
        assert config.get("CUSTOM") == 42

    def test_has(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        assert config.has("LOG_LEVEL")
        assert not config.has("DOES_NOT_EXIST")

    def test_all_returns_copy(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        all_config = config.all()
        assert isinstance(all_config, dict)
        all_config["LOG_LEVEL"] = "CORRUPTED"
        assert config.get("LOG_LEVEL") == "INFO"


class TestImmutableSettings:
    def test_cannot_set_immutable_key(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test"\nFACEBOOK_PAGE_ID=123\nFACEBOOK_ACCESS_TOKEN=tok\n'
        )
        config = ConfigManager(project_root=tmp_path).load()
        with pytest.raises(InvalidConfig):
            config.set("OPENAI_API_KEY", "sk-new-key")

    def test_cannot_set_facebook_page_id(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test"\nFACEBOOK_PAGE_ID=123\nFACEBOOK_ACCESS_TOKEN=tok\n'
        )
        config = ConfigManager(project_root=tmp_path).load()
        with pytest.raises(InvalidConfig):
            config.set("FACEBOOK_PAGE_ID", "99999")

    def test_admin_mode_allows_immutable_override(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-old"\nFACEBOOK_PAGE_ID=123\nFACEBOOK_ACCESS_TOKEN=tok\n'
        )
        config = ConfigManager(project_root=tmp_path, admin_mode=True).load()
        config.set("OPENAI_API_KEY", "sk-new-key")
        assert config.get("OPENAI_API_KEY") == "sk-new-key"

    def test_non_immutable_keys_can_be_set(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        config.set("AI_TEMPERATURE", 0.9)
        assert config.get("AI_TEMPERATURE") == 0.9

    def test_get_immutable_keys_list(self, tmp_path):
        immutable = ConfigManager(project_root=tmp_path).get_immutable_keys()
        assert "OPENAI_API_KEY" in immutable
        assert "FACEBOOK_PAGE_ID" in immutable
        assert "CONFIG_VERSION" in immutable


class TestConfigVersion:
    def test_config_version_set_on_load(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        assert config.get("CONFIG_VERSION") == CONFIG_VERSION

    def test_config_version_property(self, tmp_path):
        assert ConfigManager(project_root=tmp_path).load().config_version == CONFIG_VERSION

    def test_config_version_is_immutable(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        with pytest.raises(InvalidConfig):
            config.set("CONFIG_VERSION", 99)


class TestValidation:
    def test_validate_passes(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test123"\n'
            'FACEBOOK_PAGE_ID=12345\n'
            'FACEBOOK_ACCESS_TOKEN=abc_token\n'
            'LOG_LEVEL=INFO\n'
        )
        assert ConfigManager(project_root=tmp_path).load().validate() == []

    def test_validate_fails_missing_required(self, tmp_path):
        errors = ConfigManager(project_root=tmp_path).load().validate()
        assert len(errors) >= 3
        assert any("OPENAI_API_KEY" in e for e in errors)

    def test_validate_strict_raises(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        with pytest.raises(SchemaError):
            config.validate_strict()

    def test_validate_catches_invalid_log_level(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test"\nFACEBOOK_PAGE_ID=123\n'
            'FACEBOOK_ACCESS_TOKEN=tok\nLOG_LEVEL=MEGA_VERBOSE\n'
        )
        errors = ConfigManager(project_root=tmp_path).load().validate()
        assert any("LOG_LEVEL" in e for e in errors)


class TestSave:
    def test_save_creates_json_without_secret_values(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-super-secret"\n'
            'FACEBOOK_ACCESS_TOKEN=fb-super-secret\n'
        )
        config = ConfigManager(project_root=tmp_path).load()
        config.set("MY_KEY", "my_value")
        config.save("config/agent_config.json")
        saved = json.loads((tmp_path / "config" / "agent_config.json").read_text())
        assert saved["MY_KEY"] == "my_value"
        assert saved["CONFIG_VERSION"] == CONFIG_VERSION
        assert saved["OPENAI_API_KEY"] == "***SECRET***"
        assert saved["FACEBOOK_ACCESS_TOKEN"] == "***SECRET***"
        assert "sk-super-secret" not in (tmp_path / "config" / "agent_config.json").read_text()

    def test_save_replaces_atomically(self, tmp_path):
        config = ConfigManager(project_root=tmp_path).load()
        config.set("MY_KEY", "first")
        config.save("config/agent_config.json")
        config.set("MY_KEY", "second")
        config.save("config/agent_config.json")
        saved = json.loads((tmp_path / "config" / "agent_config.json").read_text())
        assert saved["MY_KEY"] == "second"
