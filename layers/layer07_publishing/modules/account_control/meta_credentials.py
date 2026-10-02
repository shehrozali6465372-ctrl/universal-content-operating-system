"""Compatibility facade for the canonical L11 Meta integration adapter."""
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer11_async_runtime.modules.provider_integration.meta_credentials import MetaCredentialProvider
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
__all__ = ["MetaCredentialProvider", "AccountRegistry"]
