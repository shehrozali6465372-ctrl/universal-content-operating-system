"""Canonical L11 provider gateway for external integration transport."""
from __future__ import annotations

import base64
import hashlib
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from .config import IntegrationConfig
from .http_client import HTTPClient, IntegrationConfigurationError


class IntegrationGateway:
    """Credential-bound external provider transport; no workflow ownership."""

    def __init__(
        self,
        config: Optional[IntegrationConfig] = None,
        client: Optional[HTTPClient] = None,
    ) -> None:
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
        query = query.strip()
        if not query:
            raise ValueError("query is required")
        if self.config.serpapi_key:
            response = self.http.request(
                "GET",
                "https://serpapi.com/search",
                params={
                    "engine": "google",
                    "q": query,
                    "api_key": self.config.serpapi_key,
                    "location": location,
                },
            )
            data = response.data if isinstance(response.data, dict) else {"raw": response.data}
            results = []
            for item in data.get("organic_results") or []:
                link = str(item.get("link") or "").strip()
                if link:
                    results.append(
                        {
                            "source_id": hashlib.sha256(link.encode()).hexdigest(),
                            "title": item.get("title"),
                            "link": link,
                            "snippet": item.get("snippet"),
                            "position": item.get("position"),
                        }
                    )
            return {
                "provider": "serpapi",
                "source": "google_search",
                "query": query,
                "results": results,
            }

        candidates = [query]
        tokens = [token for token in query.split() if len(token) >= 4]
        for width in (5, 3, 2):
            if len(tokens) >= width:
                candidate = " ".join(tokens[:width])
                if candidate not in candidates:
                    candidates.append(candidate)

        results = []
        selected_query = query
        for candidate in candidates:
            response = self.http.request(
                "GET",
                "https://news.google.com/rss/search",
                params={"q": candidate, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                headers={"Accept": "application/rss+xml, application/xml, text/xml"},
            )
            raw = response.data if isinstance(response.data, str) else str(response.data)
            try:
                root = ET.fromstring(raw)
            except ET.ParseError as exc:
                raise IntegrationConfigurationError(
                    "Google News RSS returned invalid XML"
                ) from exc

            candidate_results = []
            for position, item in enumerate(root.findall("./channel/item")[:8], 1):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                description = (item.findtext("description") or "").strip()
                if title and link:
                    candidate_results.append(
                        {
                            "source_id": hashlib.sha256(link.encode()).hexdigest(),
                            "title": title,
                            "link": link,
                            "snippet": description,
                            "position": position,
                        }
                    )
            if candidate_results:
                results = candidate_results
                selected_query = candidate
                break

        if not results:
            raise IntegrationConfigurationError(
                "Google News RSS returned no usable source results"
            )
        return {
            "provider": "google_news_rss",
            "source": "google_news_rss",
            "query": selected_query,
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
        body = {
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
