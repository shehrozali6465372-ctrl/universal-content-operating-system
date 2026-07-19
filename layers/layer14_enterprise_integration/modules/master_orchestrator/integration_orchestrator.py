"""IntegrationOrchestrator — master orchestrator for Layer 14."""
from __future__ import annotations
import time
from typing import Any, Dict

from ..di_container.di_container import DIContainer
from ..event_bus.event_bus_integration import EventBusIntegration
from ..config.config_validator import ConfigValidator
from ..config.config_loader import ConfigLoader
from ..logging.structured_logger import StructuredLogger
from ..health_check.health_system import HealthSystem
from ..security.security_middleware import SecurityMiddleware
from ..metrics.metrics_system import MetricsSystem
from ..async_wiring.async_bridge import AsyncBridge
from ..db_adapters.adapter_interface import InMemoryDBAdapter
from ..backup_wiring.backup_system import BackupSystem
from ..documentation.doc_generator import DocGenerator
from ..production.docker_config import DockerConfig
from ..integration.integration_framework import IntegrationFramework

class IntegrationOrchestrator:
    def __init__(self) -> None:
        self.container = DIContainer()
        self.event_bus = EventBusIntegration()
        self.config_validator = ConfigValidator()
        self.config_loader = ConfigLoader()
        self.logger = StructuredLogger(name='aios-integration')
        self.health = HealthSystem()
        self.security = SecurityMiddleware()
        self.metrics = MetricsSystem()
        self.async_bridge = AsyncBridge()
        self.db = InMemoryDBAdapter()
        self.backup = BackupSystem()
        self.doc_generator = DocGenerator()
        self.docker = DockerConfig()
        self.integration = IntegrationFramework()
        self._is_running = False
        self._start_time = 0.0

    def start(self) -> Dict[str, Any]:
        self._start_time = time.time()
        self._is_running = True
        self.db.connect()
        self.logger.info('Integration orchestrator started')
        self.metrics.increment('orchestrator_starts')
        return {'status': 'started', 'timestamp': self._start_time}

    def stop(self) -> Dict[str, Any]:
        self._is_running = False
        self.db.disconnect()
        self.async_bridge.shutdown()
        self.logger.info('Integration orchestrator stopped')
        return {'status': 'stopped', 'uptime': round(time.time() - self._start_time, 2)}

    def health_check(self) -> Dict[str, Any]:
        return self.health.check_all()

    def system_status(self) -> Dict[str, Any]:
        return {'running': self._is_running,
                'uptime': round(time.time() - self._start_time, 2) if self._start_time else 0,
                'metrics': self.metrics.export_all(),
                'db': self.db.health(),
                'security': {'rate_limiter': 'active', 'sanitizer': 'active'},
                'backups': len(self.backup.list_backups())}

    def full_report(self) -> Dict[str, Any]:
        return {'system_status': self.system_status(),
                'health': self.health_check(),
                'metrics': self.metrics.export_all(),
                'documentation': len(self.doc_generator.generate_all())}
