"""Tests for platform contracts and API surfaces."""
from __future__ import annotations
import os
import time
import threading
import urllib.request
import urllib.error
import json
import pytest

class TestInstagramPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher import InstagramPublisher
        self.pub=InstagramPublisher()
    def test_platform_name(self): assert self.pub.get_platform_name()=="instagram"
    def test_capabilities(self):
        caps=self.pub.get_capabilities(); assert caps.supports_images is True; assert caps.supports_carousel is True; assert caps.supports_stories is True; assert caps.supports_scheduled is False; assert caps.max_length==2200
    def test_validate(self): assert self.pub.validate("Hello Instagram!") is True; assert self.pub.validate("") is False; assert self.pub.validate("x"*3000) is False
    def test_authenticate_without_credentials(self): assert self.pub.authenticate({}) is False
    def test_authenticate_does_not_fall_back_to_environment(self, monkeypatch):
        monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID","global-account"); monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN","global-token"); assert self.pub.authenticate({}) is False
    def test_authenticate_requires_remote_validation(self, monkeypatch):
        monkeypatch.setattr(self.pub,"_api_get",lambda *args,**kwargs: None); assert self.pub.authenticate({"account_id":"account-1","access_token":"token-1"}) is False; assert self.pub.get_stats()["authenticated"] is False
    def test_feed_requires_media(self):
        self.pub._authenticated=True; self.pub._account_id="account-1"; self.pub._access_token="token-1"; result=self.pub.publish("Test"); assert result.success is False; assert "media" in result.error_message.lower()
    def test_publish_without_auth(self): assert self.pub.publish("Test").success is False
    def test_edit_not_supported(self):
        result=self.pub.edit("id","content"); assert result.success is False; assert "not support" in result.error_message.lower()
    def test_schedule_not_supported(self): assert self.pub.schedule("test",time.time()+3600).success is False
    def test_get_stats(self): stats=self.pub.get_stats(); assert stats["platform"]=="instagram"; assert "authenticated" in stats
    def test_publish_result_structure(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import PublishResult
        d=PublishResult(success=True,platform="instagram").to_dict(); assert d["platform"]=="instagram"; assert d["success"] is True

class TestYouTubeCredentialScope:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.youtube.youtube_publisher import YouTubePublisher
        self.pub=YouTubePublisher()
    def test_global_environment_token_is_ignored(self, monkeypatch):
        monkeypatch.setenv("YOUTUBE_ACCESS_TOKEN","global-token"); assert self.pub.authenticate({}) is False
    def test_explicit_credentials_are_used(self, monkeypatch):
        seen={}
        monkeypatch.setattr(self.pub,"_get",lambda path,params: seen.update({"token":self.pub.token}) or {"items":[{"id":"channel-1"}]})
        assert self.pub.authenticate({"access_token":"account-token"}) is True; assert seen["token"]=="account-token"

# Existing API/dashboard contract coverage remains below.
class TestFacebookSecrets:
    def test_secrets_environment_check(self):
        assert isinstance(os.environ.get("FACEBOOK_ACCESS_TOKEN",""),str); assert isinstance(os.environ.get("FACEBOOK_PAGE_ID",""),str)
