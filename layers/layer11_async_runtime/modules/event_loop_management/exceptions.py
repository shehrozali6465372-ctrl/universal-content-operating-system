"""Exceptions for Event Loop Management."""
from __future__ import annotations

class EventLoopError(Exception): pass
class LoopTimeoutError(EventLoopError): pass
class LoopRecoveryError(EventLoopError): pass
class LoopBalancingError(EventLoopError): pass
