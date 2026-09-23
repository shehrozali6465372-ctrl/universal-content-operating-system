"""Layer 1 Core runtime contract.

Layer1Runtime is the explicit lifecycle boundary for the Layer 1 foundation.
Production persistence is delegated to Layer 13; local SQLite components are
therefore intentionally development/test-only.
"""
from __future__ import annotations
from typing import Any, Dict, Optional


class Layer1Runtime:
    """Deterministic startup, readiness, health aggregation and shutdown."""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root
        self.environment = None
        self.config = None
        self.secrets = None
        self.database = None
        self.memory = None
        self.file_manager = None
        self.logger = None
        self.scheduler = None
        self.settings = None
        self.backup = None
        self._started = False

    def start(
        self,
        profile: str = "development",
        master_key: Optional[str] = None,
        env_file: str = ".env",
        strict_config: bool = False,
    ) -> "Layer1Runtime":
        from layers.layer01_core.modules.environment_loader import EnvironmentLoader
        from layers.layer01_core.modules.config_manager import ConfigManager
        from layers.layer01_core.modules.secrets_manager import SecretsManager
        from layers.layer01_core.modules.database_manager import DatabaseManager
        from layers.layer01_core.modules.memory_manager import MemoryManager
        from layers.layer01_core.modules.file_manager.file_manager import FileManager
        from layers.layer01_core.modules.logger.logger_manager import LoggerManager
        from layers.layer01_core.modules.scheduler.scheduler_manager import SchedulerManager
        from layers.layer01_core.modules.settings_manager.settings_manager import SettingsManager
        from layers.layer01_core.modules.backup_manager.backup_manager import BackupManager

        # Fail closed: do not mark readiness until every required foundation
        # component has initialized successfully.
        self.environment = EnvironmentLoader(project_root=self.project_root)
        self.environment.load(profile=profile, env_file=env_file)
        self.environment.validate_strict()

        self.config = ConfigManager(project_root=self.project_root)
        self.config.load(env_file=env_file)
        if strict_config:
            self.config.validate_strict()

        self.secrets = SecretsManager(
            project_root=self.project_root,
            secrets_path=".secrets",
            audit_log_path="logs/audit.log",
        )
        self.secrets.setup(master_key=master_key)

        self.database = DatabaseManager(
            db_path=self.config.get("DATABASE_PATH", "data/agent.db"),
            project_root=self.project_root,
        ).initialize()

        self.memory = MemoryManager(
            db_path="data/agent_memory.db",
            project_root=self.project_root,
        ).initialize()
        self.file_manager = FileManager(
            base_path=self.project_root or "."
        )
        self.logger = LoggerManager(
            log_dir=str((self.file_manager._base / "logs").resolve())
        )
        self.scheduler = SchedulerManager(
            queue_persist_path=str((self.file_manager._base / "data" / "scheduler_queue.json").resolve()),
            retry_persist_path=str((self.file_manager._base / "data" / "scheduler_retries.json").resolve()),
        )
        self.settings = SettingsManager(
            persist_path=str((self.file_manager._base / "data" / "settings.json").resolve())
        )
        self.backup = BackupManager(
            backup_dir=str((self.file_manager._base / "backups").resolve())
        )
        self._started = True
        return self

    def health_check(self) -> Dict[str, Any]:
        checks: Dict[str, Any] = {}
        components = {
            "environment": self.environment,
            "secrets": self.secrets,
            "database": self.database,
            "memory": self.memory,
            "file_manager": self.file_manager,
            "logger": self.logger,
            "scheduler": self.scheduler,
            "settings": self.settings,
            "backup": self.backup,
        }
        for name, component in components.items():
            if component is None:
                checks[name] = {"status": "FAIL", "message": "not initialized"}
                continue
            try:
                report = component.health_check()
                checks[name] = report
            except Exception as exc:
                checks[name] = {"status": "FAIL", "message": str(exc)[:300]}

        failed = [n for n, r in checks.items() if r.get("overall") == "FAIL" or r.get("status") == "FAIL"]
        ready = self._started and not failed
        return {
            "ready": ready,
            "liveness": True,
            "overall": "PASS" if ready else "FAIL",
            "checks": checks,
        }

    def shutdown(self) -> None:
        """Drain scheduling first, then close persistence resources."""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=True)
        if self.memory is not None:
            self.memory.close()
        if self.database is not None:
            self.database.close()
        self._started = False

    @property
    def is_ready(self) -> bool:
        return self._started and self.health_check()["ready"]


__all__ = ["Layer1Runtime"]
