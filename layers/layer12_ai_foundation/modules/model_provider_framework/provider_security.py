"""provider_security.py — API key and secret management."""
from __future__ import annotations
import hashlib
from typing import Any, Dict


class ProviderSecurity:
    """Manages API keys, tokens, and security for providers."""

    def __init__(self) -> None:
        self._keys: Dict[str, Dict[str, str]] = {}
        self._encrypted: Dict[str, str] = {}

    def store_key(self, provider: str, api_key: str, key_type: str = "api_key") -> None:
        if provider not in self._keys:
            self._keys[provider] = {}
        self._keys[provider][key_type] = api_key
        self._encrypted[provider] = hashlib.sha256(api_key.encode()).hexdigest()

    def get_key(self, provider: str, key_type: str = "api_key") -> str:
        return self._keys.get(provider, {}).get(key_type, "")

    def has_key(self, provider: str) -> bool:
        return provider in self._keys and len(self._keys[provider]) > 0

    def remove_key(self, provider: str, key_type: str = "api_key") -> bool:
        if provider in self._keys and key_type in self._keys[provider]:
            del self._keys[provider][key_type]
            return True
        return False

    def validate_key_format(self, provider: str, api_key: str) -> bool:
        patterns = {"openai": "sk-", "claude": "sk-ant-", "gemini": "AI"}
        prefix = patterns.get(provider, "")
        return api_key.startswith(prefix) if prefix else len(api_key) > 5

    def get_masked_key(self, provider: str) -> str:
        key = self.get_key(provider)
        if len(key) > 8:
            return key[:4] + "*" * (len(key) - 8) + key[-4:]
        return "****"

    def to_dict(self) -> Dict[str, Any]:
        return {"providers": list(self._keys.keys()),
                "has_keys": {p: self.has_key(p) for p in self._keys}}
