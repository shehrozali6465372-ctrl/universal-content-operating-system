"""
Tests for Settings Manager Module
Layer 1: Core System — Module 9

Run: python -m pytest layers/layer01_core/tests/test_settings_manager.py -v
"""

import json
import pytest
from layers.layer01_core.modules.settings_manager.settings_manager import (
    SettingsManager, validator_not_empty, validator_positive_int, validator_in_list, validator_model_exists,
)
from layers.layer01_core.modules.settings_manager.setting_schema import SettingEntry
from layers.layer01_core.modules.settings_manager.exceptions import (
    SettingNotFoundError, SettingValidationError, SettingImmutableError,
    InvalidFeatureFlagError, RollbackError, SettingsLoadError,
)


@pytest.fixture
def sm(tmp_path):
    return SettingsManager(persist_path=str(tmp_path / "settings.json"))


@pytest.fixture
def sm_prepopulated(sm):
    sm.register("AI_MODEL", "gpt-5", category="ai", validator=validator_model_exists)
    sm.register("LOG_LEVEL", "INFO", category="system")
    sm.register("POST_INTERVAL_HOURS", 4, datatype=int, category="schedule",
                validator=validator_positive_int)
    sm.register("PAGE_NAME", "MyPage", editable=True, category="facebook")
    sm.register("API_KEY", "secret-key-123", immutable=True, category="security",
                description="Do not change at runtime")
    return sm


# ── Test 1: Register Settings ────────────────

class TestRegister:
    def test_register_basic(self, sm):
        sm.register("TEST_KEY", "test_value")
        assert sm.get("TEST_KEY") == "test_value"

    def test_register_with_metadata(self, sm):
        entry = sm.register("AI_MODEL", "gpt-5", category="ai",
                           description="AI model to use")
        assert entry.key == "AI_MODEL"
        assert entry.value == "gpt-5"
        assert entry.category == "ai"
        assert entry.description == "AI model to use"

    def test_register_immutable(self, sm):
        sm.register("SECRET", "abc", immutable=True)
        entry = sm.get_entry("SECRET")
        assert entry.immutable is True

    def test_register_default_value(self, sm):
        sm.register("SETTING", "current", default_value="original")
        entry = sm.get_entry("SETTING")
        assert entry.default_value == "original"
        assert entry.value == "current"


# ── Test 2: Get / Set ───────────────────────

class TestGetSet:
    def test_get_existing(self, sm_prepopulated):
        assert sm_prepopulated.get("AI_MODEL") == "gpt-5"

    def test_get_nonexistent(self, sm):
        assert sm.get("NOPE") is None

    def test_get_with_default(self, sm):
        assert sm.get("NOPE", "fallback") == "fallback"

    def test_set_value(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        assert sm_prepopulated.get("LOG_LEVEL") == "DEBUG"

    def test_set_records_history(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        history = sm_prepopulated.get_history("LOG_LEVEL")
        assert len(history) >= 1
        assert history[-1]["old_value"] == "INFO"
        assert history[-1]["new_value"] == "DEBUG"

    def test_set_updates_version(self, sm_prepopulated):
        entry = sm_prepopulated.get_entry("LOG_LEVEL")
        v1 = entry.version
        sm_prepopulated.set("LOG_LEVEL", "WARN")
        entry2 = sm_prepopulated.get_entry("LOG_LEVEL")
        assert entry2.version == v1 + 1

    def test_set_nonexistent_raises(self, sm):
        with pytest.raises(SettingNotFoundError):
            sm.set("NOPE", "value")

    def test_set_immutable_raises(self, sm_prepopulated):
        with pytest.raises(SettingImmutableError):
            sm_prepopulated.set("API_KEY", "new-key")

    def test_set_validation_fails(self, sm_prepopulated):
        with pytest.raises(SettingValidationError):
            sm_prepopulated.set("AI_MODEL", "invalid-model")


# ── Test 3: Delete ──────────────────────────

class TestDelete:
    def test_delete_existing(self, sm_prepopulated):
        sm_prepopulated.delete("LOG_LEVEL")
        assert not sm_prepopulated.exists("LOG_LEVEL")

    def test_delete_nonexistent_raises(self, sm):
        with pytest.raises(SettingNotFoundError):
            sm.delete("NOPE")

    def test_delete_immutable_raises(self, sm_prepopulated):
        with pytest.raises(SettingImmutableError):
            sm_prepopulated.delete("API_KEY")


# ── Test 4: Keys / All / Category ───────────

class TestListing:
    def test_keys(self, sm_prepopulated):
        keys = sm_prepopulated.keys()
        assert "AI_MODEL" in keys
        assert "LOG_LEVEL" in keys

    def test_all(self, sm_prepopulated):
        all_settings = sm_prepopulated.all()
        assert all_settings["AI_MODEL"] == "gpt-5"
        assert all_settings["LOG_LEVEL"] == "INFO"

    def test_by_category(self, sm_prepopulated):
        ai = sm_prepopulated.by_category("ai")
        assert "AI_MODEL" in ai
        assert "LOG_LEVEL" not in ai

    def test_exists(self, sm_prepopulated):
        assert sm_prepopulated.exists("AI_MODEL")
        assert not sm_prepopulated.exists("NOPE")


# ── Test 5: Overrides ───────────────────────

class TestOverrides:
    def test_set_override(self, sm_prepopulated):
        sm_prepopulated.set_override("AI_MODEL", "gpt-4o")
        assert sm_prepopulated.get("AI_MODEL") == "gpt-4o"

    def test_override_highest_priority(self, sm_prepopulated):
        sm_prepopulated.set_override("AI_MODEL", "gpt-4o")
        assert sm_prepopulated.effective_value("AI_MODEL") == "gpt-4o"

    def test_clear_override(self, sm_prepopulated):
        sm_prepopulated.set_override("AI_MODEL", "gpt-4o")
        sm_prepopulated.clear_override("AI_MODEL")
        assert sm_prepopulated.get("AI_MODEL") == "gpt-5"

    def test_clear_all_overrides(self, sm_prepopulated):
        sm_prepopulated.set_override("AI_MODEL", "gpt-4o")
        sm_prepopulated.set_override("LOG_LEVEL", "DEBUG")
        count = sm_prepopulated.clear_all_overrides()
        assert count == 2

    def test_override_nonexistent_raises(self, sm):
        with pytest.raises(SettingNotFoundError):
            sm.set_override("NOPE", "value")


# ── Test 6: Feature Flags ───────────────────

class TestFeatureFlags:
    def test_register_flag(self, sm):
        sm.register_flag("dark_mode", enabled=True)
        assert sm.is_flag_active("dark_mode")

    def test_disabled_flag(self, sm):
        sm.register_flag("beta_feature", enabled=False)
        assert not sm.is_flag_active("beta_feature")

    def test_toggle_flag(self, sm):
        sm.register_flag("toggle_test", enabled=False)
        sm.toggle_flag("toggle_test")
        assert sm.is_flag_active("toggle_test")
        sm.toggle_flag("toggle_test")
        assert not sm.is_flag_active("toggle_test")

    def test_flag_with_conditions(self, sm):
        sm.register_flag("conditional", enabled=True,
                        conditions={"env": "production"})
        assert not sm.is_flag_active("conditional")
        assert sm.is_flag_active("conditional", {"env": "production"})

    def test_flag_nonexistent_raises(self, sm):
        with pytest.raises(InvalidFeatureFlagError):
            sm.is_flag_active("nope")

    def test_get_flags(self, sm):
        sm.register_flag("f1", description="Flag one")
        sm.register_flag("f2", enabled=False)
        flags = sm.get_flags()
        assert "f1" in flags
        assert "f2" in flags

    def test_flag_rollout_zero(self, sm):
        sm.register_flag("zero_rollout", rollout_pct=0)
        assert not sm.is_flag_active("zero_rollout")


# ── Test 7: History & Rollback ──────────────

class TestHistoryRollback:
    def test_history_recorded(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        sm_prepopulated.set("LOG_LEVEL", "WARN")
        history = sm_prepopulated.get_history("LOG_LEVEL")
        assert len(history) == 2

    def test_rollback(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        sm_prepopulated.set("LOG_LEVEL", "ERROR")
        sm_prepopulated.rollback("LOG_LEVEL", steps=1)
        assert sm_prepopulated.get("LOG_LEVEL") == "DEBUG"

    def test_rollback_two_steps(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "A")
        sm_prepopulated.set("LOG_LEVEL", "B")
        sm_prepopulated.set("LOG_LEVEL", "C")
        sm_prepopulated.rollback("LOG_LEVEL", steps=2)
        assert sm_prepopulated.get("LOG_LEVEL") == "A"

    def test_rollback_immutable_raises(self, sm):
        sm.register("CONST", "original", immutable=True)
        # Create history by directly recording
        sm._record_history("CONST", "original", "first_change", "test")
        with pytest.raises(SettingImmutableError):
            sm.rollback("CONST", steps=1)

    def test_rollback_insufficient_history(self, sm_prepopulated):
        with pytest.raises(RollbackError):
            sm_prepopulated.rollback("LOG_LEVEL", steps=100)

    def test_history_with_limit(self, sm_prepopulated):
        for i in range(30):
            sm_prepopulated.set("LOG_LEVEL", f"level_{i}")
        history = sm_prepopulated.get_history("LOG_LEVEL", limit=5)
        assert len(history) == 5


# ── Test 8: Import / Export ─────────────────

class TestImportExport:
    def test_export_json(self, sm_prepopulated, tmp_path):
        filepath = str(tmp_path / "export.json")
        sm_prepopulated.export_settings(filepath)
        data = json.loads(open(filepath).read())
        assert "AI_MODEL" in data

    def test_import_json(self, sm, tmp_path):
        filepath = str(tmp_path / "import.json")
        data = {"TEST": {"key": "TEST", "value": "imported", "datatype": "str",
                         "category": "general", "editable": True, "immutable": False,
                         "last_changed": "", "changed_by": "", "version": 1,
                         "description": ""}}
        open(filepath, "w").write(json.dumps(data))
        count = sm.import_settings(filepath)
        assert count == 1
        assert sm.get("TEST") == "imported"

    def test_import_nonexistent_raises(self, sm):
        with pytest.raises(SettingsLoadError):
            sm.import_settings("/no/such/file.json")

    def test_import_no_overwrite(self, sm_prepopulated, tmp_path):
        filepath = str(tmp_path / "import.json")
        data = {"AI_MODEL": {"key": "AI_MODEL", "value": "gpt-4o", "datatype": "str",
                             "category": "ai", "editable": True, "immutable": False,
                             "last_changed": "", "changed_by": "", "version": 1,
                             "description": ""}}
        open(filepath, "w").write(json.dumps(data))
        count = sm_prepopulated.import_settings(filepath, overwrite=False)
        assert count == 0  # Should not overwrite existing
        assert sm_prepopulated.get("AI_MODEL") == "gpt-5"

    def test_export_flags(self, sm, tmp_path):
        sm.register_flag("test_flag", description="Test")
        filepath = str(tmp_path / "flags.json")
        sm.export_flags(filepath)
        data = json.loads(open(filepath).read())
        assert "test_flag" in data


# ── Test 9: Event System ────────────────────

class TestEventSystem:
    def test_event_emitted_on_set(self, sm_prepopulated):
        events_received = []
        def on_change(event):
            events_received.append(event)
        sm_prepopulated.events.subscribe("setting_changed", on_change)
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        assert len(events_received) == 1
        assert events_received[0].key == "LOG_LEVEL"

    def test_global_subscriber(self, sm_prepopulated):
        events_received = []
        sm_prepopulated.events.subscribe_all(lambda e: events_received.append(e))
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        assert len(events_received) == 1

    def test_unsubscribe(self, sm_prepopulated):
        events_received = []
        handler = lambda e: events_received.append(e)
        sm_prepopulated.events.subscribe("setting_changed", handler)
        sm_prepopulated.events.unsubscribe("setting_changed", handler)
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        assert len(events_received) == 0

    def test_event_log(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        log = sm_prepopulated.events.get_event_log(key="LOG_LEVEL")
        assert len(log) >= 1

    def test_clear_event_log(self, sm_prepopulated):
        sm_prepopulated.set("LOG_LEVEL", "DEBUG")
        count = sm_prepopulated.events.clear_log()
        assert count >= 1
        assert sm_prepopulated.events.get_event_log() == []

    def test_subscriber_count(self, sm_prepopulated):
        sm_prepopulated.events.subscribe("setting_changed", lambda e: None)
        sm_prepopulated.events.subscribe_all(lambda e: None)
        assert sm_prepopulated.events.subscriber_count() >= 2


# ── Test 10: Persistence ────────────────────

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        filepath = str(tmp_path / "persist.json")
        sm1 = SettingsManager(persist_path=filepath)
        sm1.register("KEY1", "value1", category="test")
        sm1.register("KEY2", 42, datatype=int, category="test")
        sm1.register_flag("my_flag", enabled=True)
        sm1.save()

        sm2 = SettingsManager(persist_path=filepath)
        sm2.load()
        assert sm2.get("KEY1") == "value1"
        assert sm2.get("KEY2") == 42
        assert sm2.is_flag_active("my_flag")

    def test_load_nonexistent(self, sm):
        assert sm.load("/no/such/file.json") is False

    def test_save_custom_path(self, tmp_path):
        filepath = str(tmp_path / "custom.json")
        sm = SettingsManager()
        sm.register("X", "y")
        sm.save(filepath)
        assert (tmp_path / "custom.json").exists()


# ── Test 11: Validators ─────────────────────

class TestValidators:
    def test_not_empty_valid(self):
        assert validator_not_empty("hello") is True

    def test_not_empty_invalid(self):
        assert validator_not_empty("") is False
        assert validator_not_empty("  ") is False

    def test_positive_int_valid(self):
        assert validator_positive_int(5) is True

    def test_positive_int_invalid(self):
        assert validator_positive_int(-1) is False
        assert validator_positive_int("5") is False

    def test_in_list(self):
        v = validator_in_list(["a", "b", "c"])
        assert v("a") is True
        assert v("d") is False

    def test_model_exists_valid(self):
        assert validator_model_exists("gpt-5") is True

    def test_model_exists_invalid(self):
        assert validator_model_exists("gpt-99") is False


# ── Test 12: Health Check ───────────────────

class TestHealthCheck:
    def test_health_check(self, sm_prepopulated):
        sm_prepopulated.register_flag("test_flag", enabled=True)
        report = sm_prepopulated.health_check()
        assert report["overall"] == "PASS"
        assert "settings" in report["checks"]
        assert "feature_flags" in report["checks"]
        assert "overrides" in report["checks"]
        assert "history" in report["checks"]
        assert "event_bus" in report["checks"]

    def test_health_check_no_flags_warns(self, sm):
        report = sm.health_check()
        assert report["overall"] == "WARN"

    def test_health_check_message(self, sm_prepopulated):
        report = sm_prepopulated.health_check()
        assert "5 settings" in report["checks"]["settings"]["message"]


# ── Test 13: Setting Entry Schema ────────────

class TestSettingEntry:
    def test_to_dict(self):
        entry = SettingEntry("K", "V", category="cat")
        d = entry.to_dict()
        assert d["key"] == "K"
        assert d["value"] == "V"
        assert d["category"] == "cat"

    def test_from_dict(self):
        d = {"key": "K", "value": "V", "datatype": "int", "category": "cat",
             "editable": True, "immutable": False, "description": "desc",
             "last_changed": "", "changed_by": "", "version": 1}
        entry = SettingEntry.from_dict(d)
        assert entry.key == "K"
        assert entry.datatype == int

    def test_validate_passes(self):
        entry = SettingEntry("K", "V", validator=lambda v: len(v) > 0)
        assert entry.validate_value("hello") is True

    def test_validate_fails(self):
        entry = SettingEntry("K", "V", validator=lambda v: len(v) > 5)
        assert entry.validate_value("hi") is False

    def test_snapshot(self):
        entry = SettingEntry("K", "V")
        snap = entry.snapshot()
        assert snap["value"] == "V"
        assert "timestamp" in snap
