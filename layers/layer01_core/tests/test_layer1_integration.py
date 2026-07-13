"""
Layer 1 Integration Test Suite
Tests all 10 modules working together as a unified system.

Run: python -m pytest layers/layer01_core/tests/test_layer1_integration.py -v
"""

import json
import os
import pytest
from pathlib import Path

from layers.layer01_core.modules.config_manager import ConfigManager
from layers.layer01_core.modules.secrets_manager import SecretsManager
from layers.layer01_core.modules.database_manager import DatabaseManager
from layers.layer01_core.modules.memory_manager import MemoryManager
from layers.layer01_core.modules.logger.logger_manager import LoggerManager
from layers.layer01_core.modules.scheduler.scheduler_manager import SchedulerManager
from layers.layer01_core.modules.file_manager.file_manager import FileManager
from layers.layer01_core.modules.settings_manager.settings_manager import SettingsManager
from layers.layer01_core.modules.backup_manager.backup_manager import BackupManager


@pytest.fixture
def tmp_env(tmp_path):
    env = {"root": str(tmp_path)}
    for d in ["config", "data", "logs", "files", "backups"]:
        (tmp_path / d).mkdir()
    return env


@pytest.fixture
def config(tmp_env):
    return ConfigManager(project_root=tmp_env["root"])


@pytest.fixture
def secrets(tmp_env):
    sm = SecretsManager(
        secrets_path=str(Path(tmp_env["root"]) / ".secrets"),
        audit_log_path=str(Path(tmp_env["root"]) / "logs" / "audit.log"),
        project_root=tmp_env["root"],
    )
    sm.setup(master_key="test-master-key-12345")
    return sm


@pytest.fixture
def database(tmp_env):
    dm = DatabaseManager(db_path=str(Path(tmp_env["root"]) / "data" / "agent.db"),
                         project_root=tmp_env["root"])
    dm.initialize()
    return dm


@pytest.fixture
def memory(tmp_env):
    m = MemoryManager(db_path=str(Path(tmp_env["root"]) / "data" / "memory.db"),
                      project_root=tmp_env["root"])
    m.initialize()
    return m


@pytest.fixture
def logger(tmp_env):
    return LoggerManager(log_dir=str(Path(tmp_env["root"]) / "logs"))


@pytest.fixture
def scheduler():
    return SchedulerManager()


@pytest.fixture
def file_mgr(tmp_env):
    return FileManager(base_path=str(Path(tmp_env["root"]) / "files"))


@pytest.fixture
def settings(tmp_env):
    return SettingsManager(persist_path=str(Path(tmp_env["root"]) / "settings.json"))


@pytest.fixture
def backup(tmp_env):
    return BackupManager(backup_dir=str(Path(tmp_env["root"]) / "backups"))


# ── 1: Config + Secrets + Settings Pipeline ────────────────────

class TestConfigSecretsSettings:
    def test_full_config_pipeline(self, config, secrets, settings):
        settings.register("AI_MODEL", "gpt-5", category="ai")
        settings.register("LOG_LEVEL", "INFO", category="system")
        settings.register("POST_INTERVAL", 4, datatype=int, category="schedule")

        secrets.store("OPENAI_API_KEY", "sk-test-key-12345")
        secrets.store("FACEBOOK_TOKEN", "fb-token-67890")

        assert settings.get("AI_MODEL") == "gpt-5"
        assert secrets.retrieve("OPENAI_API_KEY") == "sk-test-key-12345"
        assert secrets.retrieve("FACEBOOK_TOKEN") == "fb-token-67890"

    def test_settings_override_priority(self, settings):
        settings.register("SETTING", "default_val")
        settings.set("SETTING", "runtime_val")
        settings.set_override("SETTING", "override_val")
        assert settings.get("SETTING") == "override_val"
        settings.clear_override("SETTING")
        assert settings.get("SETTING") == "runtime_val"

    def test_feature_flags_control(self, settings):
        settings.register_flag("auto_publish", enabled=True)
        settings.register_flag("beta_feature", enabled=False)
        assert settings.is_flag_active("auto_publish") is True
        assert settings.is_flag_active("beta_feature") is False
        settings.toggle_flag("beta_feature")
        assert settings.is_flag_active("beta_feature") is True


# ── 2: Database + Memory Pipeline ──────────────────────────────

class TestDatabaseMemory:
    def test_database_stores_data(self, database):
        database.query("CREATE TABLE IF NOT EXISTS agent_state (key TEXT, value TEXT)")
        database.insert("agent_state", {"key": "last_topic", "value": "finance"})
        row = database.query_one("SELECT value FROM agent_state WHERE key = 'last_topic'")
        assert row["value"] == "finance"

    def test_memory_store_and_load(self, memory):
        memory.save("stm", "task", "current_task", "writing_post")
        memory.save("ltm", "learning", "best_hooks", "question_hooks")
        memory.save("working", "plan", "today_plan", "write_3_posts")
        memory.save("episodic", "history", "post_1", "got_100_likes")

        results = memory.load(level="stm", category="task", key="current_task")
        assert len(results) >= 1
        assert results[0]["value"] == "writing_post"


# ── 3: Logger Integration ─────────────────────────────────────

class TestLoggerIntegration:
    def test_logger_records_events(self, logger):
        logger.info("system", "Agent started")
        logger.info("research", "Research completed")
        logger.warning("system", "API rate limit approaching")
        entries = logger.get_entries()
        assert len(entries) >= 3

    def test_logger_health_check(self, logger):
        report = logger.health_check()
        assert "overall" in report
        assert report["overall"] in ("PASS", "WARN")


# ── 4: Scheduler Integration ───────────────────────────────────

class TestSchedulerIntegration:
    def test_scheduler_task_execution(self, scheduler):
        results = []

        def research_task(params):
            results.append("research_done")

        scheduler.register_handler("research", research_task)
        task_id = scheduler.add_task("research_task", job_type="research")
        task = scheduler.get_task(task_id)
        scheduler.run_task(task)
        assert "research_done" in results

    def test_scheduler_health(self, scheduler):
        report = scheduler.health_check()
        assert "overall" in report


# ── 5: File Manager Integration ────────────────────────────────

class TestFileManagerIntegration:
    def test_file_manager_read_write(self, file_mgr):
        file_mgr.write("config/settings.json", json.dumps({"model": "gpt-5"}))
        content = file_mgr.read("config/settings.json")
        data = json.loads(content)
        assert data["model"] == "gpt-5"

    def test_file_manager_backup_restore(self, file_mgr):
        file_mgr.write("data.json", "original")
        backup_path = file_mgr.backup("data.json")
        file_mgr.write("data.json", "modified")
        file_mgr.restore(backup_path, "data.json")
        assert file_mgr.read("data.json") == "original"

    def test_file_manager_hash_integrity(self, file_mgr):
        file_mgr.write("important.txt", "critical data")
        file_mgr.save_and_verify("important.txt", "critical data")
        match, h = file_mgr.verify_hash("important.txt")
        assert match is True

    def test_file_manager_compression(self, file_mgr):
        file_mgr.write("big.txt", "x" * 10000)
        gz = file_mgr.compress("big.txt")
        out = file_mgr.decompress(gz)
        assert file_mgr.read(out) == "x" * 10000

    def test_file_manager_health(self, file_mgr):
        file_mgr.write("init.txt", "init")
        file_mgr.backup("init.txt")
        report = file_mgr.health_check()
        assert report["overall"] == "PASS"


# ── 6: Backup + File Manager Integration ───────────────────────

class TestBackupIntegration:
    def test_backup_of_file_data(self, file_mgr, backup):
        file_mgr.write("agent_data.json", json.dumps({"posts": 42}))
        entry = backup.backup("configs", str(Path(file_mgr._base) / "agent_data.json"))
        assert entry is not None
        assert entry.size_bytes > 0
        assert backup.verify_integrity(entry.backup_id) is True

    def test_backup_rotation(self, file_mgr, backup):
        file_mgr.write("temp.txt", "temp data")
        for i in range(5):
            backup.backup("logs", str(Path(file_mgr._base) / "temp.txt"),
                         retention_days=0)
        removed = backup.rotate()
        assert removed >= 5

    def test_backup_health(self, backup):
        report = backup.health_check()
        assert "overall" in report


# ── 7: Full Agent Workflow ─────────────────────────────────────

class TestFullWorkflow:
    def test_complete_agent_cycle(self, config, secrets, database, memory,
                                   logger, scheduler, file_mgr, settings, backup):
        # 1. Setup
        settings.register("AI_MODEL", "gpt-5", category="ai")
        settings.register("POST_INTERVAL", 4, datatype=int, category="schedule")
        settings.register_flag("auto_publish", enabled=True)
        secrets.store("FACEBOOK_TOKEN", "fb-token-test")

        # 2. Log start
        logger.info("system", "Agent cycle started")

        # 3. Store research in memory
        memory.save("working", "research", "topic", "AI in Finance")
        memory.save("working", "research", "data", "Market up 15%")

        # 4. Write post
        post_content = "AI is transforming finance. Market up 15%!"
        file_mgr.write("posts/pending_post.json", json.dumps({
            "content": post_content,
            "topic": "AI in Finance",
            "model": settings.get("AI_MODEL"),
        }))

        # 5. Log post creation
        logger.info("writing", "Post created")

        # 6. Store in database
        database.query("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, status TEXT)")
        database.insert("posts", {"content": post_content, "status": "pending"})

        # 7. Schedule publication
        scheduler.register_handler("publish", lambda p: None)
        task_id = scheduler.add_task("publish_post", job_type="publish")

        # 8. Verify all systems
        assert settings.get("AI_MODEL") == "gpt-5"
        assert secrets.retrieve("FACEBOOK_TOKEN") == "fb-token-test"
        assert settings.is_flag_active("auto_publish") is True

        post_data = json.loads(file_mgr.read("posts/pending_post.json"))
        assert post_data["content"] == post_content

        row = database.query_one("SELECT content, status FROM posts WHERE status = 'pending'")
        assert row["content"] == post_content

        topic_results = memory.load(level="working", category="research", key="topic")
        assert len(topic_results) >= 1

        # 9. Backup
        entry = backup.backup("all", str(Path(file_mgr._base) / "posts" / "pending_post.json"),
                             description="Post backup before publish")
        assert entry is not None
        assert backup.verify_integrity(entry.backup_id) is True

        # 10. Log completion
        logger.info("system", "Agent cycle completed")

        # 11. Health checks
        assert settings.health_check()["overall"] in ("PASS", "WARN")
        file_mgr.write("init.txt", "init")
        file_mgr.backup("init.txt")
        assert file_mgr.health_check()["overall"] == "PASS"
        assert backup.health_check()["overall"] in ("PASS", "WARN")


# ── 8: Event System Cross-Module ───────────────────────────────

class TestEventSystemCrossModule:
    def test_settings_events_propagate(self, settings):
        events = []
        settings.events.subscribe_all(lambda e: events.append(e))
        settings.register("X", "initial")
        settings.set("X", "changed")
        settings.set_override("X", "overridden")
        settings.clear_override("X")
        event_types = [e.event_type for e in events]
        assert "setting_changed" in event_types
        assert "override_set" in event_types
        assert "override_cleared" in event_types

    def test_settings_persistence(self, settings):
        settings.register("PERSIST_KEY", "persist_value")
        settings.save()
        settings2 = SettingsManager(persist_path=settings._persist_path)
        settings2.load()
        assert settings2.get("PERSIST_KEY") == "persist_value"


# ── 9: Error Handling Across Modules ───────────────────────────

class TestErrorHandling:
    def test_missing_setting_raises(self, settings):
        with pytest.raises(Exception):
            settings.set("NONEXISTENT", "value")

    def test_missing_secret_returns_none(self, secrets):
        assert secrets.retrieve("NONEXISTENT") is None

    def test_missing_backup_raises(self, backup):
        with pytest.raises(Exception):
            backup.restore("no_such_backup", "/tmp/out.txt")

    def test_file_manager_missing_file(self, file_mgr):
        assert file_mgr.read("nonexistent.txt") is None

    def test_memory_empty_search(self, memory):
        results = memory.search(keyword="nonexistent_query", levels=["stm"])
        assert isinstance(results, list)
