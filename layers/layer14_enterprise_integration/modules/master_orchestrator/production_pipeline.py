"""Production pipeline extensions for account isolation, policy gating, media routing and repetition regeneration."""
from __future__ import annotations

import hashlib
from typing import Any, Dict

from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
    PipelineWiring, ContentRequest, ContentResponse,
)
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
from layers.layer07_publishing.modules.media_manager.runtime_media import RuntimeMedia
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.policy_registry import PolicyRegistry
from layers.layer07_publishing.modules.account_control.policy_bootstrap import ensure_default_snapshots
from layers.layer07_publishing.modules.account_control.credential_resolver import AccountCredentialResolver


class ProductionPipeline(PipelineWiring):
    """Account-isolated production execution with explicit policy snapshots."""

    def _credentials(self, platform: str, account_id: str, credentials_ref: str) -> Dict[str, str]:
        # Meta assets share one System User secret. Derive the required Page
        # credential at runtime from the account's registered Meta asset id.
        if credentials_ref == "META_ACCESS_TOKEN" and platform in ("facebook", "instagram"):
            from layers.layer07_publishing.modules.account_control.meta_credentials import MetaCredentialProvider
            return MetaCredentialProvider().credentials_for(platform, account_id)
        credentials = AccountCredentialResolver.resolve(credentials_ref)
        if not credentials:
            return {}
        if platform == "facebook":
            return {"page_id": credentials.get("page_id", credentials.get("account_id", "")), "access_token": credentials.get("access_token", "")}
        if platform == "instagram":
            return {"account_id": credentials.get("account_id", ""), "access_token": credentials.get("access_token", "")}
        if platform == "pinterest":
            return {"access_token": credentials.get("access_token", credentials.get("token", "")), "board_id": credentials.get("board_id", "")}
        if platform in ("youtube", "tiktok"):
            return {"access_token": credentials.get("access_token", credentials.get("token", ""))}
        return {}

    def _verify_public_submission(self, publisher: Any, req: ContentRequest, post_id: str) -> bool:
        """Require provider-side read evidence before consuming a production reservation."""
        try:
            post = publisher.get_post(str(post_id))
        except Exception:
            return False
        if not post:
            return False
        if req.platform == "facebook":
            account_id = str(req.metadata.get("account_id") or "")
            owner = str(((post.get("from") or {}).get("id")) or "")
            return bool(
                post.get("is_published") is True
                and post.get("is_hidden") is not True
                and (not owner or owner == account_id)
                and post.get("permalink_url")
            )
        return True

    def _publisher(self, req: ContentRequest):
        from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
        manager = PublisherManager()
        publisher = manager.plugin_manager.registry.get_instance(req.platform)
        account_id = req.metadata.get("account_id")
        credentials_ref = req.metadata.get("credentials_ref")
        if publisher is None or not account_id or not credentials_ref:
            return None, manager
        credentials = self._credentials(req.platform, str(account_id), str(credentials_ref))
        if not credentials or not publisher.authenticate(credentials):
            return None, manager
        return manager, publisher

    def _policy_check(self, req: ContentRequest, response: ContentResponse) -> None:
        registry = ensure_default_snapshots(PolicyRegistry())
        policy = registry.get(req.platform, req.metadata.get("policy_version"))
        if policy is None:
            raise RuntimeError(f"no policy snapshot registered for {req.platform}; production publishing blocked")
        types = policy.constraints.get("content_types")
        if types and req.metadata.get("content_type") not in types:
            raise RuntimeError(f"content type {req.metadata.get('content_type')} is not allowed by policy {policy.version}")
        max_len = policy.constraints.get("max_length")
        if max_len is not None and len(response.text) > int(max_len):
            raise RuntimeError(f"content exceeds policy max_length={max_len}")
        response.quality_report = (response.quality_report or {}) | {
            "policy_version": policy.version,
            "policy_source": policy.source,
            "policy_scope": policy.content_gate.get("scope"),
        }

    def _publish(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
        from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset

        publish_mode = str(req.metadata.get("publish_mode") or "production").strip().lower()
        if publish_mode not in {"staging", "production"}:
            raise RuntimeError("publish_mode must be 'staging' or 'production'")
        if publish_mode == "production" and ctx.get("ai_model") == "offline-draft":
            raise RuntimeError("production publish boundary rejected offline-draft output")
        account_id = str(req.metadata.get("account_id") or "")
        if not account_id:
            raise RuntimeError("production publishing requires account_id")
        registry = AccountRegistry()
        account = registry.get(account_id)
        if account is None:
            raise RuntimeError(f"account {account_id!r} is not registered")
        if not account.enabled:
            raise RuntimeError(f"account {account_id!r} is disabled")
        if account.platform != req.platform:
            raise RuntimeError(f"account {account_id!r} is registered for {account.platform}, not {req.platform}")

        registered_ref = str(account.credentials_ref or "")
        requested_ref = str(req.metadata.get("credentials_ref") or "")
        if not registered_ref:
            raise RuntimeError(f"account {account_id!r} has no credential reference")
        if requested_ref and requested_ref != registered_ref:
            raise RuntimeError(f"credentials_ref does not belong to account {account_id!r}")
        req.metadata["credentials_ref"] = registered_ref

        self._policy_check(req, response)
        workspace = registry.workspace_path(account_id)
        guard = ContentRepetitionGuard(str(workspace / "publishing_history.sqlite3"))
        if publish_mode == "production" and guard.has_unresolved(account_id, req.platform):
            raise RuntimeError(
                f"unresolved publication intent already exists for account={account_id} platform={req.platform}; reconcile before creating a new publish intent"
            )
        reservation = guard.reserve(account_id=account_id, platform=req.platform, content=response.text, template_id=req.metadata.get("template_id"))
        retries = 0
        while not reservation.allowed and retries < 3:
            retries += 1
            original_style = req.style
            req.style = f"{original_style}; structural variation {retries}: different hook, paragraph pattern and CTA; do not reuse the previous template"
            self._ai(req, ctx, response)
            self._quality(req, response)
            self._policy_check(req, response)
            reservation = guard.reserve(account_id=account_id, platform=req.platform, content=response.text, template_id=None)
            req.style = original_style
        if not reservation.allowed:
            raise RuntimeError(f"content uniqueness gate rejected after regeneration: {reservation.reason}")

        request_template_fingerprint = reservation.template_fingerprint
        manager, publisher = self._publisher(req)
        if manager is None:
            guard.release(reservation.reservation_id)
            response.publish_result = {
                "success": False, "platform": req.platform, "post_id": None, "url": None,
                "error": "No account-scoped credentials/real publisher adapter configured",
                "metadata": {"template_fingerprint": request_template_fingerprint},
            }
            return {"published": False, "skipped": True, "reason": "publisher_unconfigured"}

        content_type = req.metadata.get("content_type") or ("photo" if response.image_url else "post")
        if req.platform == "instagram" and content_type == "video":
            content_type = "reel"
        media_path = response.image_url
        if req.metadata.get("content_type") == "video":
            media_path = RuntimeMedia.image_to_video(media_path, account_id)
        public_media = RuntimeMedia.public_url(media_path) if media_path else ""
        if req.platform in ("pinterest", "tiktok", "instagram"):
            if not public_media:
                guard.release(reservation.reservation_id)
                raise RuntimeError("public media URL is required for this platform")
            media_for_api = public_media
        else:
            media_for_api = media_path

        request = PublishRequest(platform=req.platform, content=response.text, content_type=content_type)
        workflow_id = str(req.metadata.get("workflow_id") or req.metadata.get("lineage_id") or request.request_id)
        request.idempotency_key = f"ucos:{account_id}:{req.platform}:{workflow_id}"
        request.metadata.update({
            "account_id": account_id,
            # ProductionPipeline owns the repetition reservation lifecycle.
            "repetition_reserved_by_pipeline": True,
            "topic": req.topic,
            "niche": req.metadata.get("niche"),
            "ai_model": ctx.get("ai_model", "unknown"),
            "policy_version": req.metadata.get("policy_version"),
            "product": req.metadata.get("product"),
            "affiliate": req.metadata.get("affiliate"),
            "template_fingerprint": request_template_fingerprint,
            "publish_mode": publish_mode,
            "workflow_id": workflow_id,
        })
        if media_for_api:
            asset = MediaAsset(
                file_path=media_for_api,
                media_type="video" if req.metadata.get("content_type") == "video" else "image",
            )
            asset.file_name = str(media_for_api).rsplit("/", 1)[-1]
            asset.platform_ready = True
            request.media_assets.append(asset)

        try:
            result = manager.publish(request)
            metadata = dict(result.metadata or {})
            data = {
                "success": bool(result.success),
                "platform": req.platform,
                "post_id": result.post_id or None,
                "url": result.url or None,
                "error": result.error_message,
                "metadata": metadata | {"template_fingerprint": request_template_fingerprint},
            }
            response.publish_result = data
            if result.success:
                if not result.post_id:
                    guard.release(reservation.reservation_id)
                    raise RuntimeError("publisher reported success without a real post_id")
                if publish_mode == "staging":
                    guard.release(reservation.reservation_id)
                    response.publish_package = request.to_dict()
                    data["metadata"] = dict(data.get("metadata") or {}) | {
                        "publish_mode": "staging", "production_counted": False
                    }
                    return data
                verified = self._verify_public_submission(publisher, req, result.post_id)
                if verified:
                    guard.finalize(reservation.reservation_id, result.post_id)
                    response.publish_package = request.to_dict()
                    ctx["post_id"] = result.post_id
                    data["metadata"] = dict(data.get("metadata") or {}) | {
                        "verified_public": True, "publish_mode": "production"
                    }
                    return data
                guard.mark_pending(reservation.reservation_id, result.post_id)
                data.update({
                    "pending": True,
                    "metadata": dict(data.get("metadata") or {}) | {
                        "verified_public": False, "publish_mode": "production"
                    },
                })
                response.publish_result = data
                return {
                    "published": False, "pending": True, "platform": req.platform,
                    "post_id": result.post_id, "reason": "awaiting_public_verification"
                }
            if metadata.get("outcome") == "unknown":
                guard.mark_pending(
                    reservation.reservation_id,
                    str(metadata.get("tracking_id") or "outcome-unknown"),
                )
                data.update({"pending": True, "reason": "outcome_unknown"})
                response.publish_result = data
                return {
                    "published": False, "pending": True,
                    "platform": req.platform, "reason": "outcome_unknown"
                }
            if metadata.get("publish_state") in {"processing", "pending"} and metadata.get("tracking_id"):
                tracking_id = str(metadata["tracking_id"])
                guard.mark_pending(reservation.reservation_id, tracking_id)
                data.update({"pending": True, "tracking_id": tracking_id})
                response.publish_result = data
                return {"published": False, "pending": True, "platform": req.platform, "tracking_id": tracking_id, "reason": "awaiting_platform_confirmation"}
            guard.release(reservation.reservation_id)
            raise RuntimeError(result.error_message or "publisher returned failure")
        except Exception:
            if not (response.publish_result or {}).get("pending"):
                try:
                    guard.release(reservation.reservation_id)
                except Exception:
                    pass
            raise
