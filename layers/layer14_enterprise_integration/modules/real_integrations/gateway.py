"""Real provider gateway: search, affiliate data, analytics and website publishing."""
from __future__ import annotations

import base64
import hashlib
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from .config import IntegrationConfig
from .http_client import HTTPClient, IntegrationConfigurationError


class IntegrationGateway:
    """Credential-bound adapters; missing credentials always fail closed."""

    def __init__(self, config: Optional[IntegrationConfig] = None, client: Optional[HTTPClient] = None) -> None:
        self.config = config or IntegrationConfig.from_env()
        validation = self.config.validation()
        if not validation["valid"]:
            raise IntegrationConfigurationError(
                "invalid integration configuration: " + "; ".join(validation["errors"])
            )
        self.http = client or HTTPClient(
            self.config.http_timeout_seconds,
            self.config.http_max_retries,
        )

    def status(self) -> Dict[str, Any]:
        return {"providers": self.config.status(), "real_only": True}

    def search(self, query: str, *, location: Optional[str] = None) -> Dict[str, Any]:
        if not self.config.serpapi_key:
            raise IntegrationConfigurationError(
                "UCOS_SERPAPI_API_KEY is required for real search/SEO data"
            )
        if not query.strip():
            raise ValueError("query is required")
        response = self.http.request(
            "GET",
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": query.strip(),
                "api_key": self.config.serpapi_key,
                "location": location,
            },
        )
        data = response.data if isinstance(response.data, dict) else {"raw": response.data}
        results = []
        for item in data.get("organic_results") or []:
            link = str(item.get("link") or "").strip()
            if not link:
                continue
            results.append({
                "source_id": hashlib.sha256(link.encode()).hexdigest(),
                "title": item.get("title"),
                "link": link,
                "snippet": item.get("snippet"),
                "position": item.get("position"),
            })
        return {
            "provider": "serpapi",
            "source": "google_search",
            "query": query.strip(),
            "results": results,
        }

    def affiliate_search(self, query: str) -> Dict[str, Any]:
        if not self.config.affiliate_base_url or not self.config.affiliate_api_key:
            raise IntegrationConfigurationError(
                "affiliate network base URL and API key are required"
            )
        path = self.config.affiliate_search_path
        path = path if path.startswith("/") else "/" + path
        response = self.http.request(
            "GET",
            urljoin(self.config.affiliate_base_url + "/", path.lstrip("/")),
            params={"q": query},
            headers={"Authorization": f"Bearer {self.config.affiliate_api_key}"},
        )
        return {
            "provider": "affiliate_network",
            "source": "affiliate_api",
            "query": query,
            "data": response.data,
        }

    def analytics_report(
        self,
        start_date: str,
        end_date: str,
        dimensions: list[str],
        metrics: list[str],
    ) -> Dict[str, Any]:
        if not self.config.ga4_property_id or not self.config.ga4_access_token:
            raise IntegrationConfigurationError(
                "GA4 property ID and OAuth access token are required"
            )
        body: Dict[str, Any] = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": name} for name in dimensions],
            "metrics": [{"name": name} for name in metrics],
        }
        headers = {"Authorization": f"Bearer {self.config.ga4_access_token}"}
        if self.config.ga4_project_id:
            headers["x-goog-user-project"] = self.config.ga4_project_id
        url = (
            "https://analyticsdata.googleapis.com/v1beta/properties/"
            f"{self.config.ga4_property_id}:runReport"
        )
        response = self.http.request("POST", url, headers=headers, json_body=body)
        return {
            "provider": "google_analytics_4",
            "source": "ga4_data_api",
            "property_id": self.config.ga4_property_id,
            "data": response.data,
        }

    def wordpress_publish(
        self,
        *,
        title: str,
        content: str,
        status: str = "draft",
    ) -> Dict[str, Any]:
        if not (
            self.config.wordpress_url
            and self.config.wordpress_username
            and self.config.wordpress_application_password
        ):
            raise IntegrationConfigurationError(
                "WordPress URL, username and application password are required"
            )
        if status not in {"draft", "publish", "pending", "private", "future"}:
            raise ValueError("unsupported WordPress post status")
        token = base64.b64encode(
            f"{self.config.wordpress_username}:{self.config.wordpress_application_password}".encode()
        ).decode()
        url = urljoin(self.config.wordpress_url + "/", "wp-json/wp/v2/posts")
        response = self.http.request(
            "POST",
            url,
            headers={"Authorization": f"Basic {token}"},
            json_body={"title": title, "content": content, "status": status},
            accepted_statuses=(201,),
        )
        data = response.data if isinstance(response.data, dict) else {"raw": response.data}
        post_id = data.get("id")
        if not post_id:
            raise RuntimeError("WordPress reported success without a real post id")
        return {
            "provider": "wordpress",
            "source": "wordpress_rest",
            "post_id": str(post_id),
            "url": data.get("link"),
            "data": data,
        }
