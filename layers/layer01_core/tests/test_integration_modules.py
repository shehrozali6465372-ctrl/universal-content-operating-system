"""
Integration Tests for Layer 1 Core Modules
Module 1: Config Manager + Module 2: Secrets Manager + Module 3: Environment Loader

Run: python -m pytest layers/layer01_core/tests/test_integration_modules.py -v
"""

import os
import pytest
from layers.layer01_core.modules.config_manager import ConfigManager
from layers.layer01_core.modules.secrets_manager import SecretsManager, FERNET_AVAILABLE
from layers.layer01_core.modules.environment_loader import EnvironmentLoader


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up singletons and env vars."""
    ConfigManager.reset()
    for key in list(os.environ.keys()):
        if key.startswith("AGENT_"):
            del os.environ[key]
    yield
    ConfigManager.reset()


class TestConfigAndEnvironmentIntegration:
    """Test that Config Manager and Environment Loader work together."""

    def test_env_loader_feeds_config_manager(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test"\nFACEBOOK_PAGE_ID=123\n'
            'FACEBOOK_ACCESS_TOKEN=tok\nLOG_LEVEL=DEBUG\n'
        )
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "default.yaml").write_text("AI_MODEL: gpt-4\n")

        # Load environment
        env_loader = EnvironmentLoader(project_root=str(tmp_path))
        env_loader.load(profile="dev")

        # Feed into config manager
        config = ConfigManager(project_root=tmp_path)
        config.load()

        # Both should have the values
        assert config.get("LOG_LEVEL") == "DEBUG"  # .env overrides YAML
        assert env_loader.get("LOG_LEVEL") == "DEBUG"  # from profile override

    def test_agent_env_override_affects_both(self, tmp_path):
        os.environ["AGENT_LOG_LEVEL"] = "ERROR"

        env_loader = EnvironmentLoader(project_root=str(tmp_path))
        env_loader.load(profile="dev")

        config = ConfigManager(project_root=tmp_path)
        config.load()

        assert env_loader.get("LOG_LEVEL") == "ERROR"


class TestSecretsAndConfigIntegration:
    """Test that Secrets Manager and Config Manager coordinate."""

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_config_provides_keys_for_secrets(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-test"\nFACEBOOK_PAGE_ID=123\nFACEBOOK_ACCESS_TOKEN=tok\n'
        )

        # Load config
        config = ConfigManager(project_root=tmp_path)
        config.load()

        # Store secret using config value
        sm = SecretsManager(
            secrets_path=str(tmp_path / ".secrets"),
            audit_log_path=str(tmp_path / "logs/audit.log"),
            project_root=str(tmp_path),
        )
        sm.setup(master_key="integration-test-key-1234")

        api_key = config.get("OPENAI_API_KEY")
        sm.store("OPENAI_API_KEY", api_key)

        # Retrieve and verify
        retrieved = sm.retrieve("OPENAI_API_KEY")
        assert retrieved == "sk-test"

        # Audit should have entries
        logs = sm.get_audit_logs()
        assert len(logs) >= 1


class TestAllThreeModulesIntegration:
    """Full integration: all 3 modules working together."""

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_full_workflow(self, tmp_path):
        (tmp_path / ".env").write_text(
            'OPENAI_API_KEY="sk-real-key"\nFACEBOOK_PAGE_ID=9999\n'
            'FACEBOOK_ACCESS_TOKEN=fb_real_token\nLOG_LEVEL=INFO\n'
        )

        # 1) Environment Loader
        env = EnvironmentLoader(project_root=str(tmp_path))
        env.load(profile="prod")
        assert env.get("FACEBOOK_PAGE_ID") == "9999"
        assert env.current_profile == "production"

        # 2) Config Manager
        config = ConfigManager(project_root=tmp_path)
        config.load()
        assert config.get("LOG_LEVEL") == "INFO"  # from .env

        # 3) Secrets Manager
        sm = SecretsManager(
            secrets_path=str(tmp_path / ".secrets"),
            audit_log_path=str(tmp_path / "logs/audit.log"),
            project_root=str(tmp_path),
        )
        sm.setup(master_key="full-test-key-1234")
        sm.store("FACEBOOK_ACCESS_TOKEN", env.get("FACEBOOK_ACCESS_TOKEN"))
        assert sm.retrieve("FACEBOOK_ACCESS_TOKEN") == "fb_real_token"

        # 4) Health checks
        env_report = env.health_check()
        health_report = sm.health_check()

        assert env_report["overall"] in ("PASS", "WARN")
        assert health_report["overall"] == "PASS"

        # 5) Snapshots
        snap = env.snapshot(str(tmp_path / "data/env_snap.json"))
        assert snap["profile"] == "production"
        assert snap["variables"]["FACEBOOK_ACCESS_TOKEN"] == "***SECRET***"
