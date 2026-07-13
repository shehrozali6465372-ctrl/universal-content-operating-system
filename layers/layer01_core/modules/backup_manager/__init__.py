"""
Backup & Recovery Module
Layer 1: Core System — Module 10

Comprehensive data protection with:
- Multi-source backup (DB, memory, logs, configs, prompts, images)
- Encrypted backups with integrity verification
- Auto backup rotation and compression
- Disaster recovery with restore wizard
- Backup scheduling and health monitoring
"""

from layers.layer01_core.modules.backup_manager.backup_manager import BackupManager
from layers.layer01_core.modules.backup_manager.backup_entry import BackupEntry

__all__ = ["BackupManager", "BackupEntry"]
