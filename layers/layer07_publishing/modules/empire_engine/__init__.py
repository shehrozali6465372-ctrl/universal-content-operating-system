"""Empire Automation Engine — Phase 10."""
from .empire_engine_manager import EmpireEngineManager, get_empire_engine
from .account_registry import AccountRegistry, get_account_registry
from .account_assignment_engine import AccountAssignmentEngine, get_assignment_engine
from .content_distribution_engine import ContentDistributionEngine, get_content_distribution
from .publishing_scheduler import PublishingScheduler, get_publishing_scheduler
from .cross_platform_sync import CrossPlatformSync, get_cross_platform_sync
from .account_health_monitor import AccountHealthMonitor, get_account_health_monitor
from .scaling_engine import ScalingEngine, get_scaling_engine

__all__ = [
    "EmpireEngineManager", "get_empire_engine",
    "AccountRegistry", "get_account_registry",
    "AccountAssignmentEngine", "get_assignment_engine",
    "ContentDistributionEngine", "get_content_distribution",
    "PublishingScheduler", "get_publishing_scheduler",
    "CrossPlatformSync", "get_cross_platform_sync",
    "AccountHealthMonitor", "get_account_health_monitor",
    "ScalingEngine", "get_scaling_engine",
]
