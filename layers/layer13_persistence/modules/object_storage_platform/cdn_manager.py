"""cdn_manager.py — CDN integration."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class CDNConfig:
    """CDN configuration."""
    __slots__ = ("provider", "domain", "distribution_id", "origins", "enabled")

    def __init__(self, provider: str = "cloudflare", domain: str = "") -> None:
        self.provider = provider
        self.domain = domain
        self.distribution_id: str = ""
        self.origins: List[str] = []
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "domain": self.domain,
                "enabled": self.enabled}


class CDNManager:
    """Manages CDN configuration and URLs."""

    def __init__(self) -> None:
        self._configs: Dict[str, CDNConfig] = {}
        self._cache_rules: Dict[str, int] = {}

    def add_config(self, name: str, config: CDNConfig) -> None:
        self._configs[name] = config

    def get_config(self, name: str) -> Optional[CDNConfig]:
        return self._configs.get(name)

    def get_url(self, config_name: str, object_key: str) -> str:
        config = self._configs.get(config_name)
        if config and config.domain:
            return f"https://{config.domain}/{object_key}"
        return f"/{object_key}"

    def set_cache_ttl(self, pattern: str, ttl_seconds: int) -> None:
        self._cache_rules[pattern] = ttl_seconds

    def get_cache_ttl(self, pattern: str) -> int:
        return self._cache_rules.get(pattern, 3600)

    def list_configs(self) -> Dict[str, CDNConfig]:
        return dict(self._configs)
