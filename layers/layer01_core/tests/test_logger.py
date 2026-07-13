"""
Tests for Logger Module
Layer 1: Core System — Module 6

Run: python -m pytest layers/layer01_core/tests/test_logger.py -v
"""

import os
import json
import pytest
from layers.layer01_core.modules.logger.logger_manager import LoggerManager, LogLevel, LOG_LEVEL_PRIORITY
from layers.layer01_core.modules.logger.log_rotation import LogRotation
from layers.layer01_core.modules.logger.decision_logger import DecisionLogger
from layers.layer01_core.modules.logger.log_rotation import LogRotation


@pytest.fixture(autouse=True)
def reset():
    LoggerManager.reset()
    yield
    LoggerManager.reset()


@pytest.fixture
def logger(tmp_path):
    return LoggerManager(
        log_dir=str(tmp_path / "logs"),
        min_level="DEBUG",
        enable_console=False,
    )


@pytest.fixture
def rotator(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return LogRotation(log_dir=str(log_dir), max_size_mb=0, max_backups=3)


@pytest.fixture
def dlogger(tmp_path):
    return DecisionLogger(log_path=str(tmp_path / "logs" / "decisions.log"))


# ── Test 1: Singleton ──────────────────────

class TestSingleton:
    def test_returns_same_instance(self, logger):
        l2 = LoggerManager()
        assert logger is l2


# ── Test 2: Log Levels ─────────────────────

class TestLogLevels:
    def test_all_9_levels_exist(self):
        assert len(LogLevel) == 9

    def test_level_priority_order(self):
        assert LOG_LEVEL_PRIORITY[LogLevel.TRACE] < LOG_LEVEL_PRIORITY[LogLevel.DEBUG]
        assert LOG_LEVEL_PRIORITY[LogLevel.DEBUG] < LOG_LEVEL_PRIORITY[LogLevel.INFO]
        assert LOG_LEVEL_PRIORITY[LogLevel.INFO] < LOG_LEVEL_PRIORITY[LogLevel.WARNING]
        assert LOG_LEVEL_PRIORITY[LogLevel.WARNING] < LOG_LEVEL_PRIORITY[LogLevel.ERROR]
        assert LOG_LEVEL_PRIORITY[LogLevel.ERROR] < LOG_LEVEL_PRIORITY[LogLevel.CRITICAL]
        assert LOG_LEVEL_PRIORITY[LogLevel.CRITICAL] < LOG_LEVEL_PRIORITY[LogLevel.SECURITY]

    def test_success_between_info_and_warning(self):
        assert LOG_LEVEL_PRIORITY[LogLevel.INFO] < LOG_LEVEL_PRIORITY[LogLevel.SUCCESS]
        assert LOG_LEVEL_PRIORITY[LogLevel.SUCCESS] < LOG_LEVEL_PRIORITY[LogLevel.WARNING]


# ── Test 3: Core Logging ───────────────────

class TestCoreLogging:
    def test_log_returns_entry(self, logger):
        entry = logger.log("INFO", "test", "Hello world")
        assert entry["level"] == "INFO"
        assert entry["module"] == "test"
        assert entry["message"] == "Hello world"

    def test_log_with_details(self, logger):
        entry = logger.log("ERROR", "db", "Connection failed", {"host": "localhost"})
        assert entry["details"]["host"] == "localhost"

    def test_convenience_methods(self, logger):
        logger.trace("m", "t")
        logger.debug("m", "d")
        logger.info("m", "i")
        logger.success("m", "s")
        logger.warning("m", "w")
        logger.error("m", "e")
        logger.critical("m", "c")
        logger.security("m", "s")
        logger.audit("m", "a")
        assert len(logger._entries) == 8  # TRACE filtered by min_level=DEBUG

    def test_min_level_filter(self, tmp_path):
        l = LoggerManager(log_dir=str(tmp_path / "logs"), min_level="WARNING", enable_console=False)
        l.info("m", "should be filtered")
        l.warning("m", "should pass")
        l.error("m", "should pass")
        assert len(l._entries) == 2
        l.reset()


# ── Test 4: Query ──────────────────────────

class TestQuery:
    def test_get_by_level(self, logger):
        logger.info("m", "msg1")
        logger.error("m", "msg2")
        logger.info("m", "msg3")
        errors = logger.get_entries(level="ERROR")
        assert len(errors) == 1

    def test_get_by_module(self, logger):
        logger.info("db", "msg1")
        logger.info("api", "msg2")
        db_logs = logger.get_entries(module="db")
        assert len(db_logs) == 1

    def test_get_limit(self, logger):
        for i in range(20):
            logger.info("m", f"msg{i}")
        result = logger.get_entries(limit=5)
        assert len(result) == 5

    def test_count_by_level(self, logger):
        logger.info("m", "a")
        logger.error("m", "b")
        logger.error("m", "c")
        counts = logger.count_by_level()
        assert counts["INFO"] == 1
        assert counts["ERROR"] == 2

    def test_count_by_module(self, logger):
        logger.info("db", "a")
        logger.info("db", "b")
        logger.info("api", "c")
        counts = logger.count_by_module()
        assert counts["db"] == 2
        assert counts["api"] == 1


# ── Test 5: File Output ────────────────────

class TestFileOutput:
    def test_writes_to_log_file(self, logger):
        logger.info("test", "file test")
        log_file = logger._log_dir / "agent.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "file test" in content

    def test_json_format_in_file(self, logger):
        logger.info("test", "json test")
        log_file = logger._log_dir / "agent.log"
        lines = log_file.read_text().strip().split("\n")
        entry = json.loads(lines[-1])
        assert entry["level"] == "INFO"

    def test_get_from_file(self, logger):
        logger.info("test", "read me")
        entries = logger.get_from_file()
        assert any("read me" in e["message"] for e in entries)


# ── Test 6: Export ─────────────────────────

class TestExport:
    def test_export_json(self, logger):
        logger.info("m", "export me")
        path = logger.export_json("export.json")
        assert path.exists()
        data = json.loads(path.read_text())
        assert len(data) >= 1


# ── Test 7: Log Rotation ───────────────────

class TestLogRotation:
    def test_needs_rotation_small_file(self, tmp_path):
        (tmp_path / "logs").mkdir()
        rotator = LogRotation(log_dir=str(tmp_path / "logs"), max_size_mb=1, max_backups=3)
        log_path = rotator.log_dir / "test.log"
        log_path.write_text("small content")
        assert rotator.needs_rotation("test.log") is False

    def test_needs_rotation_empty(self, rotator):
        assert rotator.needs_rotation("nonexistent.log") is False

    def test_rotate_creates_backup(self, rotator):
        log_path = rotator.log_dir / "test.log"
        log_path.write_text("x" * 100)  # max_size_mb=0 means any file rotates
        result = rotator.rotate("test.log")
        assert result is not None
        assert result.exists()
        assert result.name.endswith(".gz")

    def test_rotate_truncates_original(self, rotator):
        log_path = rotator.log_dir / "test.log"
        log_path.write_text("x" * 100)
        rotator.rotate("test.log")
        assert log_path.stat().st_size == 0

    def test_cleanup_old_backups(self, rotator):
        # Create more backups than max_backups (3)
        for i in range(5):
            (rotator.log_dir / f"test.log.2026010{i}_000000.gz").write_bytes(b"data")
        rotator._cleanup_old_backups("test.log")
        backups = rotator.get_backups("test.log")
        assert len(backups) <= 3

    def test_get_log_size(self, rotator):
        (rotator.log_dir / "test.log").write_text("content")
        assert rotator.get_log_size("test.log") > 0

    def test_get_total_size(self, rotator):
        (rotator.log_dir / "a.log").write_text("aaa")
        (rotator.log_dir / "b.log").write_text("bb")
        assert rotator.get_total_size() > 0


# ── Test 8: Decision Logger ────────────────

class TestDecisionLogger:
    def test_log_decision(self, dlogger):
        entry = dlogger.log_decision(
            question="Why finance topic?",
            answer="Finance posts had 28% higher engagement",
            confidence=0.92,
            data_sources=["analytics", "memory"],
            reasoning="Past 30 days data analysis",
        )
        assert entry["confidence"] == 0.92
        assert "analytics" in entry["data_sources"]

    def test_confidence_clamped(self, dlogger):
        entry = dlogger.log_decision(
            question="Q", answer="A", confidence=1.5,
            data_sources=[], reasoning="R",
        )
        assert entry["confidence"] == 1.0

    def test_get_decisions(self, dlogger):
        dlogger.log_decision("Q1", "A1", 0.9, ["src1"], "R1", module="db")
        dlogger.log_decision("Q2", "A2", 0.8, ["src2"], "R2", module="api")
        assert len(dlogger.get_decisions()) == 2
        assert len(dlogger.get_decisions(module="db")) == 1

    def test_average_confidence(self, dlogger):
        dlogger.log_decision("Q", "A", 0.8, [], "R")
        dlogger.log_decision("Q", "A", 0.6, [], "R")
        avg = dlogger.get_average_confidence()
        assert abs(avg - 0.7) < 0.01

    def test_decision_stats(self, dlogger):
        dlogger.log_decision("Q", "A", 0.9, ["analytics"], "R")
        stats = dlogger.get_decision_stats()
        assert stats["total"] == 1
        assert stats["avg_confidence"] == 0.9

    def test_persists_to_file(self, dlogger):
        dlogger.log_decision("Q", "A", 0.5, [], "R")
        file_entries = dlogger.get_from_file()
        assert len(file_entries) == 1

    def test_clear(self, dlogger):
        dlogger.log_decision("Q", "A", 0.5, [], "R")
        dlogger.clear()
        assert len(dlogger._decisions) == 0


# ── Test 9: Health Check ───────────────────

class TestHealthCheck:
    def test_health_check(self, logger):
        report = logger.health_check()
        assert report["overall"] == "PASS"
        assert "log_dir" in report["checks"]
        assert "entries" in report["checks"]
