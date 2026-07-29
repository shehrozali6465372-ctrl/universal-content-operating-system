"""Custom exceptions for Automation Engine."""


class AutomationError(Exception):
    """Base automation error."""


class TriggerError(AutomationError):
    """Trigger configuration or execution error."""


class RuleEngineError(AutomationError):
    """Rule evaluation error."""


class WorkerError(AutomationError):
    """Background worker error."""


class ScalingError(AutomationError):
    """Auto-scaling error."""


class SafetyError(AutomationError):
    """Safety violation error."""


class RecoveryError(AutomationError):
    """Emergency recovery error."""


class PipelineError(AutomationError):
    """Pipeline execution error."""


class CronError(AutomationError):
    """Cron scheduling error."""


class RetryError(AutomationError):
    """Smart retry error."""


class OptimizationError(AutomationError):
    """Workflow optimization error."""


class MonitoringError(AutomationError):
    """Automation monitoring error."""
