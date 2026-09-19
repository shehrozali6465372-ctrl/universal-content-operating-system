"""AtoZ Product Hub integration adapter for UCOS Layer 23.

The repositories remain separate. This adapter exposes only the documented
AIOS.Job.Request transport surface and calls real Layer 23 operations.
"""

from __future__ import annotations

import uuid
from typing import Any

from layers.layer23_website_manager import get_website
from layers.layer23_website_manager.pinterest_pin_manager.pinterest_pin_manager import get_pin_manager

SUPPORTED_JOB_TYPES = {
    "content",
    "seo_metadata",
    "pinterest_assets",
    "analytics_insights",
}


def _uuid(value: Any, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"{field} must be a valid UUID") from exc


def dispatch_job(data: dict[str, Any]) -> dict[str, Any]:
    """Dispatch an AIOS job into Layer 23 using real data only."""
    request_id = _uuid(data.get("request_id"), "request_id")
    niche_id = _uuid(data.get("niche_id"), "niche_id")
    job_type = str(data.get("job_type") or "").strip()
    if job_type not in SUPPORTED_JOB_TYPES:
        raise ValueError(f"unsupported job_type: {job_type}")

    context = data.get("context")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    domain = str(context.get("domain") or "").strip()
    site_name = str(context.get("site_name") or "").strip()
    if not domain or not site_name:
        raise ValueError("context.domain and context.site_name are required")

    site = get_website(domain=domain, site_name=site_name)
    job_id = str(uuid.uuid4())

    if job_type == "content":
        title = str(context.get("title") or "").strip()
        body = str(context.get("content") or "").strip()
        if not title or not body:
            raise ValueError("content jobs require real context.title and context.content")
        article = site.create_article(
            title=title,
            content=body,
            category=str(context.get("category") or ""),
            tags=list(context.get("tags") or []),
            author=str(context.get("author") or "AtozProductHub"),
            featured_image=str(context.get("featured_image") or ""),
            meta_title=str(context.get("meta_title") or ""),
            meta_description=str(context.get("meta_description") or ""),
            status="published" if bool(context.get("publish")) else "draft",
        )
        return {
            "job_id": job_id,
            "request_id": request_id,
            "niche_id": niche_id,
            "state": "succeeded",
            "result_ref": f"layer23:article:{article.article_id}",
            "result": article.to_dict(),
        }

    if job_type == "seo_metadata":
        article_id = str(context.get("article_id") or "").strip()
        if not article_id:
            raise ValueError("seo_metadata jobs require context.article_id")
        metadata = site.generate_article_seo(article_id)
        if metadata is None:
            raise LookupError(f"article not found: {article_id}")
        return {
            "job_id": job_id,
            "request_id": request_id,
            "niche_id": niche_id,
            "state": "succeeded",
            "result_ref": f"layer23:seo:{article_id}",
            "result": metadata.to_dict(),
        }

    if job_type == "pinterest_assets":
        title = str(context.get("title") or "").strip()
        website_url = str(context.get("website_url") or "").strip()
        account_id = str(context.get("account_id") or "").strip()
        board_id = str(context.get("board_id") or "").strip()
        image_path = str(context.get("image_path") or "").strip()
        if not title or not website_url or not account_id or not board_id or not image_path:
            raise ValueError(
                "pinterest_assets jobs require title, website_url, account_id, board_id and image_path"
            )
        pin = get_pin_manager().create_pin(
            pin_title=title,
            account_id=account_id,
            board_id=board_id,
            description=str(context.get("description") or ""),
            website_url=website_url,
            image_path=image_path,
            niche=str(context.get("niche") or ""),
            keywords=list(context.get("keywords") or []),
        )
        return {
            "job_id": job_id,
            "request_id": request_id,
            "niche_id": niche_id,
            "state": "succeeded",
            "result_ref": f"layer23:pinterest-pin:{pin.pin_id}",
            "result": pin.to_dict(),
            "published": False,
        }

    if job_type == "analytics_insights":
        return {
            "job_id": job_id,
            "request_id": request_id,
            "niche_id": niche_id,
            "state": "succeeded",
            "result_ref": "layer23:website:status",
            "result": site.get_status(),
        }

    raise NotImplementedError(job_type)
