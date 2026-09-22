"""Credential-safe configuration for real external integrations."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict
from urllib.parse import urlsplit


@dataclass(frozen=True)
class IntegrationConfig:
    serpapi_key: str = ""
    affiliate_base_url: str = ""
    affiliate_api_key: str = ""
    affiliate_search_path: str = "/search"
    ga4_property_id: str = ""
    ga4_access_token: str = ""
    ga4_project_id: str = ""
    wordpress_url: str = ""
    wordpress_username: str = ""
    wordpress_application_password: str = ""
    http_timeout_seconds: float = 20.0
    http_max_retries: int = 3

    @classmethod
    def from_env(cls) -> "IntegrationConfig":
        return cls(
            serpapi_key=os.getenv("UCOS_SERPAPI_API_KEY", ""),
            affiliate_base_url=os.getenv("UCOS_AFFILIATE_BASE_URL", "").rstrip("/"),
            affiliate_api_key=os.getenv("UCOS_AFFILIATE_API_KEY", ""),
            affiliate_search_path=os.getenv("UCOS_AFFILIATE_SEARCH_PATH", "/search"),
            ga4_property_id=os.getenv("UCOS_GA4_PROPERTY_ID", ""),
            ga4_access_token=os.getenv("UCOS_GA4_ACCESS_TOKEN", ""),
            ga4_project_id=os.getenv("UCOS_GA4_PROJECT_ID", ""),
            wordpress_url=os.getenv("UCOS_WORDPRESS_URL", "").rstrip("/"),
            wordpress_username=os.getenv("UCOS_WORDPRESS_USERNAME", ""),
            wordpress_application_password=os.getenv("UCOS_WORDPRESS_APPLICATION_PASSWORD", ""),
            http_timeout_seconds=float(os.getenv("UCOS_HTTP_TIMEOUT_SECONDS", "20")),
            http_max_retries=max(1, int(os.getenv("UCOS_HTTP_MAX_RETRIES", "3"))),
        )

    @staticmethod
    def _https(url: str) -> bool:
        return urlsplit(url).scheme.lower() == "https"

    def validation(self) -> Dict[str, object]:
        production = os.getenv("APP_ENV", "development").lower() in {"production", "prod"}
        errors = []
        for name, url in (("affiliate_base_url", self.affiliate_base_url), ("wordpress_url", self.wordpress_url)):
            if url and production and not self._https(url):
                errors.append(f"{name} must use HTTPS in production")
        if self.http_timeout_seconds <= 0:
            errors.append("http_timeout_seconds must be > 0")
        if self.http_max_retries < 1:
            errors.append("http_max_retries must be >= 1")
        return {"valid": not errors, "errors": errors}

    def status(self) -> Dict[str, object]:
        return {
            "serpapi": bool(self.serpapi_key),
            "affiliate_network": bool(self.affiliate_base_url and self.affiliate_api_key),
            "google_analytics_4": bool(self.ga4_property_id and self.ga4_access_token),
            "wordpress": bool(self.wordpress_url and self.wordpress_username and self.wordpress_application_password),
            "validation": self.validation(),
        }
