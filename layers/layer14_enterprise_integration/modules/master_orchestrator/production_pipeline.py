"""Production pipeline extensions for account isolation, policy gating and publication."""
from __future__ import annotations

from typing import Any, Dict

from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
    PipelineWiring, ContentRequest, ContentResponse,
)
from layers.layer20_image_pipeline.modules.media_lifecycle.runtime_media import RuntimeMedia
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.policy_registry import PolicyRegistry
from layers.layer07_publishing.modules.account_control.policy_bootstrap import ensure_default_snapshots
from layers.layer07_publishing.modules.account_control.meta_credentials import MetaCredentialProvider
from layers.layer17_security.modules.credential_resolver.credential_resolver import AccountCredentialResolver


class ProductionPipeline(PipelineWiring):
    """Account-isolated orchestration; L07 owns durable publication semantics."""

    @staticmethod
    def _production() -> bool:
        import os
        return os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}

    def _credentials(self, platform: str, account_id: str, credentials_ref: str) -> Dict[str, str]:
        if credentials_ref == "META_ACCESS_TOKEN" and platform in ("facebook", "instagram"):
            return MetaCredentialProvider().credentials_for(platform, account_id)
        credentials = AccountCredentialResolver.resolve(credentials_ref, account_id)
        if not credentials:
            return {}
        if platform == "facebook":
            return {
                "page_id": credentials.get("page_id", credentials.get("account_id", "")),
                "access_token": credentials.get("access_token", ""),
            }
        if platform == "instagram":
            return {
                "account_id": credentials.get("account_id", ""),
                "access_token": credentials.get("access_token", ""),
            }
        if platform == "pinterest":
            return {
                "access_token": credentials.get("access_token", credentials.get("token", "")),
                "board_id": credentials.get("board_id", ""),
            }
        if platform in ("youtube", "tiktok"):
            return {"access_token": credentials.get("access_token", credentials.get("token", ""))}
        return {}

    def _publisher(self, req: ContentRequest):
        from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
        manager = PublisherManager()
        account_id = str(req.metadata.get("account_id") or "")
        credentials_ref = str(req.metadata.get("credentials_ref") or "")
        publisher = manager.plugin_manager.registry.get_instance(req.platform)
        if publisher is None or not account_id or not credentials_ref:
            return None, manager
        credentials = self._credentials(req.platform, account_id, credentials_ref)
        if req.platform == "facebook":
            platform_account_id = str(credentials.get("page_id") or "")
        elif req.platform == "instagram":
            platform_account_id = str(credentials.get("account_id") or "")
        else:
            platform_account_id = str(
                credentials.get("platform_account_id")
                or credentials.get("account_id")
                or credentials.get("board_id")
                or ""
            )
        if platform_account_id:
            req.metadata["platform_account_id"] = platform_account_id
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
            raise RuntimeError(
                f"content type {req.metadata.get('content_type')} is not allowed by policy {policy.version}"
            )
        max_len = policy.constraints.get("max_length")
        if max_len is not None and len(response.text) > int(max_len):
            raise RuntimeError(f"content exceeds policy max_length={max_len}")
        response.quality_report = (response.quality_report or {}) | {
            "policy_version": policy.version,
            "policy_source": policy.source,
            "policy_scope": policy.content_gate.get("scope"),
        }
        req.metadata["policy_snapshot"] = {
            "version": policy.version,
            "source": policy.source,
            "scope": policy.content_gate.get("scope"),
            "constraints": policy.constraints,
        }

    def _publish(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str, Any]) -> Dict[str, Any]:
        import os
        from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
        from layers.layer20_image_pipeline.modules.media_lifecycle.media_asset import MediaAsset

        publish_mode = str(ctx.get("effective_publish_mode") or req.metadata.get("publish_mode") or "").strip().lower()
        account_id = str(req.metadata.get("account_id") or "").strip()
        if not account_id:
            raise RuntimeError("production publishing requires account_id")

        registry = AccountRegistry()
        account = registry.get(account_id)
        if account is None:
            raise RuntimeError(f"account {account_id!r} is not registered")
        if not account.enabled:
            raise RuntimeError(f"account {account_id!r} is disabled")
        if account.platform != req.platform:
            raise RuntimeError(
                f"account {account_id!r} is registered for {account.platform}, not {req.platform}"
            )

        registered_identity = {
            "tenant_id": str(account.tenant_id or ""),
            "workspace_id": str(account.workspace_id or ""),
            "brand_id": str(account.brand_id or ""),
            "platform_account_id": str(account.platform_account_id or ""),
            "credentials_ref": str(account.credentials_ref or ""),
        }
        for field, canonical_value in registered_identity.items():
            supplied = str(req.metadata.get(field) or "").strip()
            if supplied and supplied != canonical_value:
                raise RuntimeError(f"{field} does not match canonical account identity")
            req.metadata[field] = canonical_value

        registered_ref = str(account.credentials_ref or "")
        requested_ref = str(req.metadata.get("credentials_ref") or "")
        if not registered_ref:
            raise RuntimeError(f"account {account_id!r} has no credential reference")
        if requested_ref and requested_ref != registered_ref:
            raise RuntimeError(f"credentials_ref does not belong to account {account_id!r}")
        req.metadata["credentials_ref"] = registered_ref
        if publish_mode not in {"staging", "production"}:
            raise RuntimeError("effective publish mode was not resolved by server preflight")
        if publish_mode == "production" and ctx.get("ai_model") == "offline-draft":
            raise RuntimeError("production publish boundary rejected offline-draft output")


        if publish_mode == "production":
            for field in ("tenant_id", "workspace_id", "brand_id"):
                if not str(req.metadata.get(field) or "").strip():
                    raise RuntimeError(f"{field} is required for production publication")

        self._policy_check(req, response)
        manager, publisher = self._publisher(req)
        if manager is None or publisher is None:
            response.publish_result = {
                "success": False,
                "platform": req.platform,
                "post_id": None,
                "url": None,
                "error": "No account-scoped credentials/real publisher adapter configured",
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
                raise RuntimeError("public media URL is required for this platform")
            media_for_api = public_media
        else:
            media_for_api = media_path

        request = PublishRequest(platform=req.platform, content=response.text, content_type=content_type)
        workflow_id = str(req.metadata.get("workflow_id") or req.metadata.get("lineage_id") or "").strip()
        if not workflow_id:
            raise RuntimeError("workflow_id is required for production publication")
        request.idempotency_key = f"ucos:{account_id}:{req.platform}:{workflow_id}"
        request.metadata.update({
            "account_id": account_id,
            "tenant_id": str(req.metadata.get("tenant_id") or ""),
            "workspace_id": str(req.metadata.get("workspace_id") or ""),
            "brand_id": str(req.metadata.get("brand_id") or ""),
            "platform_account_id": str(req.metadata.get("platform_account_id") or ""),
            "topic": req.topic,
            "niche": req.metadata.get("niche"),
            "ai_model": ctx.get("ai_model", "unknown"),
            "policy_version": req.metadata.get("policy_version"),
            "policy_snapshot": req.metadata.get("policy_snapshot"),
            "product": req.metadata.get("product"),
            "affiliate": req.metadata.get("affiliate"),
            "template_id": req.metadata.get("template_id"),
            "requested_visibility": req.metadata.get("requested_visibility") or "PUBLIC",
            "publish_mode": publish_mode,
            "workflow_id": workflow_id,
            "publish_operation_id": req.metadata.get("publish_operation_id") or "",
        })
        if req.metadata.get("tracked_link_ref"):
            request.metadata["tracked_link_ref"] = req.metadata["tracked_link_ref"]

        if media_for_api:
            asset = MediaAsset(
                file_path=media_for_api,
                media_type="video" if req.metadata.get("content_type") == "video" else "image",
            )
            asset.file_name = str(media_for_api).rsplit("/", 1)[-1]
            asset.platform_ready = True
            request.media_assets.append(asset)

        # Repetition protection is owned by the canonical PostgreSQL publication ledger.
        # Do not reintroduce the removed SQLite/content-history guard here.
        result = manager.publish(request)
        metadata = dict(result.metadata or {})
        if metadata.get("outcome") == "unknown":
            response.publish_result = {
                "success": False,
                "platform": req.platform,
                "post_id": None,
                "url": None,
                "error": result.error_message or "provider outcome unknown; reconciliation required",
                "metadata": metadata,
            }
            return {"published": False, "pending": True, "reason": "reconciliation_required"}
        data = {
            "success": bool(result.success),
            "platform": req.platform,
            "post_id": result.post_id or None,
            "url": result.url or None,
            "error": result.error_message,
            "metadata": metadata,
        }
        response.publish_result = data

        if result.success:
            verified = self._verify_public_submission(req, result)
            if not verified:
                raise RuntimeError("provider effect not independently verified; reconciliation required")
            response.publish_package = request.to_dict()
            ctx["post_id"] = result.post_id
            return data

        if metadata.get("pending"):
            response.publish_result = data
            return {
                "published": False,
                "pending": True,
                "platform": req.platform,
                "intent_id": metadata.get("publication_intent_id"),
                "publication_state": metadata.get("publication_state"),
                "reason": metadata.get("reason") or "reconciliation_required",
            }

        if metadata.get("publication_blocked"):
            raise RuntimeError(result.error_message or "publication blocked by canonical ledger")
        raise RuntimeError(result.error_message or "publisher returned failure")

    def _verify_public_submission(self, request: ContentRequest, result: Any) -> bool:
        metadata = dict(getattr(result, "metadata", {}) or {})
        return metadata.get("verified") is True

    def execute(self, request: ContentRequest) -> ContentResponse:
        # Make the workflow identity explicit for the frozen durable contracts.
        import uuid
        request.metadata.setdefault("workflow_id", request.metadata.get("lineage_id") or str(uuid.uuid4()))
        return super().execute(request)
