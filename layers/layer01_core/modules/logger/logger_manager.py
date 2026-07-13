"""
Logger Manager Module
Layer 1: Core System — Module 6

Central logger with 9 levels, structured JSON output, colored console.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
from threading import Lock


class LogLevel(str, Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"
    AUDIT = "AUDIT"


LOG_LEVEL_PRIORITY = {
    LogLevel.TRACE: 0, LogLevel.DEBUG: 10, LogLevel.INFO: 20,
    LogLevel.SUCCESS: 25, LogLevel.WARNING: 30, LogLevel.ERROR: 40,
    LogLevel.CRITICAL: 50, LogLevel.SECURITY: 60, LogLevel.AUDIT: 70,
}

# Console colors
LOG_COLORS = {
    LogLevel.TRACE: "\033[90m",      # Gray
    LogLevel.DEBUG: "\033[36m",      # Cyan
    LogLevel.INFO: "\033[37m",       # White
    LogLevel.SUCCESS: "\033[92m",    # Green
    LogLevel.WARNING: "\033[93m",    # Yellow
    LogLevel.ERROR: "\033[91m",      # Red
    LogLevel.CRITICAL: "\033[1;91m", # Bold Red
    LogLevel.SECURITY: "\033[95m",   # Magenta
    LogLevel.AUDIT: "\033[94m",      # Blue
}
RESET = "\033[0m"


class LoggerManager:
    """Central logging manager with structured output and rotation."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        log_dir: str = "logs",
        min_level: str = "DEBUG",
        enable_console: bool = True,
        enable_file: bool = True,
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._min_level = LogLevel(min_level.upper())
        self._enable_console = enable_console
        self._enable_file = enable_file
        self._entries: List[Dict] = []
        self._lock = Lock()

    # ── Core Log Method ────────────────────

    def log(
        self,
        level: str,
        module: str,
        message: str,
        details: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Write a single log entry."""
        log_level = LogLevel(level.upper())
        if LOG_LEVEL_PRIORITY[log_level] < LOG_LEVEL_PRIORITY[self._min_level]:
            return {}

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": log_level.value,
            "module": module,
            "message": message,
        }
        if details:
            entry["details"] = details

        with self._lock:
            self._entries.append(entry)

        if self._enable_console:
            self._print_colored(entry)
        if self._enable_file:
            self._write_to_file(entry)

        return entry

    # ── Convenience Methods ─────────────────

    def trace(self, module: str, message: str, **kwargs):
        return self.log("TRACE", module, message, kwargs or None)

    def debug(self, module: str, message: str, **kwargs):
        return self.log("DEBUG", module, message, kwargs or None)

    def info(self, module: str, message: str, **kwargs):
        return self.log("INFO", module, message, kwargs or None)

    def success(self, module: str, message: str, **kwargs):
        return self.log("SUCCESS", module, message, kwargs or None)

    def warning(self, module: str, message: str, **kwargs):
        return self.log("WARNING", module, message, kwargs or None)

    def error(self, module: str, message: str, **kwargs):
        return self.log("ERROR", module, message, kwargs or None)

    def critical(self, module: str, message: str, **kwargs):
        return self.log("CRITICAL", module, message, kwargs or None)

    def security(self, module: str, message: str, **kwargs):
        return self.log("SECURITY", module, message, kwargs or None)

    def audit(self, module: str, message: str, **kwargs):
        return self.log("AUDIT", module, message, kwargs or None)

    # ── File Output ─────────────────────────

    def _write_to_file(self, entry: Dict) -> None:
        log_file = self._log_dir / "agent.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def _print_colored(self, entry: Dict) -> None:
        level = LogLevel(entry["level"])
        color = LOG_COLORS.get(level, "")
        ts = entry["timestamp"][:19]
        mod = entry["module"]
        msg = entry["message"]
        print(f"{color}[{ts}] [{level.value:8s}] [{mod}] {msg}{RESET}", file=sys.stderr)

    # ── Query ───────────────────────────────

    def get_entries(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get log entries with optional filters."""
        entries = self._entries
        if level:
            entries = [e for e in entries if e["level"] == level.upper()]
        if module:
            entries = [e for e in entries if e["module"] == module]
        return entries[-limit:]

    def get_from_file(self, limit: int = 100) -> List[Dict]:
        """Read last N entries from log file."""
        log_file = self._log_dir / "agent.log"
        if not log_file.exists():
            return []
        entries = []
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries[-limit:]

    def count_by_level(self) -> Dict[str, int]:
        """Count entries by level."""
        counts = {}
        for e in self._entries:
            counts[e["level"]] = counts.get(e["level"], 0) + 1
        return counts

    def count_by_module(self) -> Dict[str, int]:
        """Count entries by module."""
        counts = {}
        for e in self._entries:
            counts[e["module"]] = counts.get(e["module"], 0) + 1
        return counts

    # ── Export ──────────────────────────────

    def export_json(self, filepath: str) -> Path:
        """Export all entries to JSON file."""
        path = self._log_dir / filepath
        with open(path, "w") as f:
            json.dump(self._entries, f, indent=2, default=str)
        return path

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        report["checks"]["log_dir"] = {
            "status": "PASS" if self._log_dir.exists() else "FAIL",
            "message": f"Log directory: {self._log_dir}",
        }
        report["checks"]["entries"] = {
            "status": "PASS",
            "message": f"{len(self._entries)} entries in memory",
        }
        log_file = self._log_dir / "agent.log"
        if log_file.exists():
            size_kb = log_file.stat().st_size / 1024
            report["checks"]["log_file"] = {
                "status": "PASS" if size_kb < 10240 else "WARN",
                "message": f"agent.log: {size_kb:.1f} KB",
            }
        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report

    # ── Reset ───────────────────────────────

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._instance = None
