"""Tests for Layer 1: Core Intelligence

Updated to match actual layer01_core module structure.
"""

from layers.layer01_core.modules.config_manager import ConfigManager
from layers.layer01_core.modules.memory_manager import MemoryManager
from layers.layer01_core.modules.logger.logger_manager import LoggerManager


class TestConfigManager:
    def setup_method(self):
        self.config = ConfigManager()

    def test_initialization(self):
        assert self.config is not None

    def test_has_get_method(self):
        assert hasattr(self.config, 'get')


class TestMemoryManager:
    def setup_method(self):
        self.memory = MemoryManager()

    def test_initialization(self):
        assert self.memory is not None

    def test_has_store_method(self):
        assert hasattr(self.memory, 'store') or hasattr(self.memory, 'save')


class TestLoggerManager:
    def setup_method(self):
        self.logger = LoggerManager()

    def test_initialization(self):
        assert self.logger is not None

    def test_has_log_method(self):
        assert hasattr(self.logger, 'log') or hasattr(self.logger, 'info')
