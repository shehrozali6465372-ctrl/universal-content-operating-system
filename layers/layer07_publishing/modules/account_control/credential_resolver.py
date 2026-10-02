"""Backward-compatible facade for the L17 credential-resolution boundary.

Credential ownership and resolution live in Layer 17.  This symbol remains only
so legacy callers do not silently fork a second credential implementation.
"""
from __future__ import annotations

from layers.layer17_security.modules.credential_resolver.credential_resolver import (
    AccountCredentialResolver,
)

__all__ = ["AccountCredentialResolver"]
