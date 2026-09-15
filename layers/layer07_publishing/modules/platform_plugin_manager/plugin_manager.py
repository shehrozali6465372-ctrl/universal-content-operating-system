"""Plugin Manager — canonical registration for all production platform adapters."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PublishResult, PlatformCapabilities
from layers.layer07_publishing.modules.platform_plugin_manager.plugin_registry import PluginRegistry
from layers.layer07_publishing.modules.platform_plugin_manager.exceptions import PluginNotFoundError, AuthenticationError

class PluginManager:
    def __init__(self, registry: Optional[PluginRegistry] = None) -> None:
        self.registry = registry or PluginRegistry(); self._operation_count=0; self._register_builtin_plugins()
    def _register_builtin_plugins(self):
        builtins={
            "facebook":("layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher","FacebookPublisher"),
            "instagram":("layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher","InstagramPublisher"),
            "pinterest":("layers.layer07_publishing.modules.platform_plugin_manager.pinterest.pinterest_publisher","PinterestPublisher"),
            "youtube":("layers.layer07_publishing.modules.platform_plugin_manager.youtube.youtube_publisher","YouTubePublisher"),
            "tiktok":("layers.layer07_publishing.modules.platform_plugin_manager.tiktok.tiktok_publisher","TikTokPublisher"),
        }
        import importlib
        for platform,(module,name) in builtins.items():
            if self.registry.is_registered(platform): continue
            try: self.registry.register(platform,getattr(importlib.import_module(module),name))
            except Exception: pass
    def register(self,platform,publisher_class): self.registry.register(platform,publisher_class)
    def authenticate(self,platform,credentials):
        p=self._get_or_raise(platform); ok=p.authenticate(credentials); self._operation_count+=1
        if not ok: raise AuthenticationError(f"Auth failed for {platform}")
        return ok
    def publish(self,platform,content,media_paths=None,content_type="post",**kwargs):
        p=self._get_or_raise(platform); r=p.publish(content,media_paths,content_type,**kwargs); self._operation_count+=1; return r
    def edit(self,platform,post_id,content,**kwargs): return self._get_or_raise(platform).edit(post_id,content,**kwargs)
    def delete(self,platform,post_id): return self._get_or_raise(platform).delete(post_id)
    def get_post(self,platform,post_id): return self._get_or_raise(platform).get_post(post_id)
    def get_status(self,platform,post_id): return self._get_or_raise(platform).get_status(post_id)
    def get_analytics(self,platform,post_id): return self._get_or_raise(platform).get_analytics(post_id)
    def get_capabilities(self,platform): return self._get_or_raise(platform).get_capabilities()
    def get_all_capabilities(self): return self.registry.list_capabilities()
    def supports(self,platform,feature): return self.get_capabilities(platform).supports(feature)
    def find_platforms_with_feature(self,feature): return [p for p in self.registry.list_platforms() if self.supports(p,feature)]
    def _get_or_raise(self,platform)->BasePublisher:
        p=self.registry.get_instance(platform)
        if p is None: raise PluginNotFoundError(f"No plugin registered for '{platform}'")
        return p
    @property
    def operation_count(self): return self._operation_count
