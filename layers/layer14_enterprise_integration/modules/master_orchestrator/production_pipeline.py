"""Production pipeline extensions for account isolation, media routing and repetition regeneration."""
from __future__ import annotations
import hashlib, os
from pathlib import Path
from typing import Any, Dict
from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring, ContentRequest, ContentResponse
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
from layers.layer07_publishing.modules.media_manager.runtime_media import RuntimeMedia

class ProductionPipeline(PipelineWiring):
    """Canonical pipeline with production platform credential routing.

    Account identity is mandatory for the production path. The adapter receives
    only credentials belonging to that account; no cross-account fallback exists.
    """
    def _credentials(self, platform: str, account_id: str) -> Dict[str,str]:
        prefix={"facebook":"FACEBOOK","instagram":"INSTAGRAM","pinterest":"PINTEREST","youtube":"YOUTUBE","tiktok":"TIKTOK"}.get(platform.upper(),platform.upper())
        c={}
        if platform in ("facebook","instagram"):
            c["account_id"]=os.environ.get(f"{prefix}_ACCOUNT_ID","") or os.environ.get("INSTAGRAM_ACCOUNT_ID","")
            c["page_id"]=os.environ.get("FACEBOOK_PAGE_ID","")
            c["access_token"]=os.environ.get("FACEBOOK_ACCESS_TOKEN","")
        elif platform=="pinterest":
            c={"access_token":os.environ.get("PINTEREST_ACCESS_TOKEN",""),"board_id":os.environ.get("PINTEREST_BOARD_ID","")}
        elif platform=="youtube": c={"access_token":os.environ.get("YOUTUBE_ACCESS_TOKEN","")}
        elif platform=="tiktok": c={"access_token":os.environ.get("TIKTOK_ACCESS_TOKEN","")}
        return c
    def _publisher(self, req: ContentRequest):
        from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
        manager=PublisherManager(); publisher=manager.plugin_manager.registry.get_instance(req.platform)
        account_id=req.metadata.get("account_id")
        if publisher is None or not account_id: return None, manager
        credentials=self._credentials(req.platform,account_id)
        if not credentials or not publisher.authenticate(credentials): return None, manager
        return manager,publisher
    def _publish(self, req: ContentRequest, response: ContentResponse, ctx: Dict[str,Any]) -> Dict[str,Any]:
        from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
        from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
        account_id=str(req.metadata.get("account_id") or "")
        if not account_id: raise RuntimeError("production publishing requires account_id")
        workspace=Path(os.environ.get("UCOS_ACCOUNT_WORKSPACES","./data/accounts/workspaces"))/account_id
        guard=ContentRepetitionGuard(str(workspace/"publishing_history.sqlite3"))
        reservation=guard.reserve(account_id=account_id,platform=req.platform,content=response.text,template_id=req.metadata.get("template_id"))
        retries=0
        while not reservation.allowed and retries<3:
            retries+=1
            original_style=req.style
            req.style=f"{original_style}; structural variation {retries}: use a different hook, paragraph pattern and CTA; do not reuse the previous template"
            self._ai(req,ctx,response)
            self._quality(req,response)
            reservation=guard.reserve(account_id=account_id,platform=req.platform,content=response.text,template_id=None)
            req.style=original_style
        if not reservation.allowed: raise RuntimeError(f"content uniqueness gate rejected after regeneration: {reservation.reason}")
        manager,_=self._publisher(req)
        if manager is None:
            guard.release(reservation.reservation_id); response.publish_result={"success":False,"platform":req.platform,"post_id":None,"url":None,"error":"No real publisher credentials/adapter configured"}; return {"published":False,"skipped":True,"reason":"publisher_unconfigured"}
        content_type=req.metadata.get("content_type") or ("photo" if response.image_url else "post")
        media_path=response.image_url
        if content_type=="video":
            media_path=RuntimeMedia.image_to_video(media_path,account_id)
        public_media=RuntimeMedia.public_url(media_path) if media_path else ""
        if req.platform in ("pinterest","tiktok","instagram") and public_media: media_for_api=public_media
        elif req.platform in ("pinterest","tiktok","instagram"): guard.release(reservation.reservation_id); raise RuntimeError("public media URL is required for this platform")
        else: media_for_api=media_path
        request=PublishRequest(platform=req.platform,content=response.text,content_type=content_type)
        request.idempotency_key=f"ucos:{account_id}:{req.platform}:{hashlib.sha256(response.text.encode()).hexdigest()[:24]}"
        request.metadata.update({"account_id":account_id,"topic":req.topic,"niche":req.metadata.get("niche"),"ai_model":ctx.get("ai_model","unknown")})
        if media_for_api:
            asset=MediaAsset(file_path=media_for_api,media_type="video" if content_type=="video" else "image")
            asset.file_name=str(media_for_api).rsplit("/",1)[-1]; asset.platform_ready=True; request.media_assets.append(asset)
        try:
            result=manager.publish(request)
            data={"success":bool(result.success),"platform":req.platform,"post_id":result.post_id,"url":result.url,"error":result.error_message}
            response.publish_result=data
            if result.success:
                guard.finalize(reservation.reservation_id,result.post_id); response.publish_package=request.to_dict(); ctx["post_id"]=result.post_id; return data
            guard.release(reservation.reservation_id); raise RuntimeError(result.error_message or "publisher returned failure")
        except Exception:
            try: guard.release(reservation.reservation_id)
            except Exception: pass
            raise
