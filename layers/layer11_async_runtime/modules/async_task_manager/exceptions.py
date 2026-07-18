"""Exceptions module."""
from __future__ import annotations

class BaseError(Exception): pass
class TaskError(BaseError): pass
class TaskTimeoutError(BaseError): pass
class TaskCancelledError(BaseError): pass
class TaskDependencyError(BaseError): pass
class TaskRetryError(BaseError): pass
