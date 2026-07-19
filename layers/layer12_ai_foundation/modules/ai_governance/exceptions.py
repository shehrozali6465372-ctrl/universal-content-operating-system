"""Custom exceptions for AI Governance."""
from __future__ import annotations
class GovernanceError(Exception): pass
class PolicyViolationError(GovernanceError): pass
class EthicsViolationError(GovernanceError): pass
class CopyrightViolationError(GovernanceError): pass
class PrivacyViolationError(GovernanceError): pass
class SafetyViolationError(GovernanceError): pass
