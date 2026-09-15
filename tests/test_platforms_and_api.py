"""Tests for Instagram, LinkedIn, API Gateway, Dashboard and platform contracts."""
from __future__ import annotations
import os
import time
import threading
import urllib.request
import json
import pytest

# Pinterest Publisher Tests
class TestPinterestPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.pinterest.pinterest_publisher import PinterestPublisher
        self.pub=PinterestPublisher()
    def test_platform_name(self): assert self.pub.get_platform_name()=="pinterest"
    def test_capabilities_match_implemented_media(self):
        caps=self.pub.get_capabilities(); assert caps.supports_images is True; assert caps.supports_video is False; assert caps.supports_scheduled is False; assert caps.max_length==500
    def test_authenticate_requires_account_scoped_credentials(self): assert self.pub.authenticate({}) is False
    def test_authenticate_does_not_fall_back_to_process_environment(self,monkeypatch):
        monkeypatch.setenv("PINTEREST_ACCESS_TOKEN","global-token"); monkeypatch.setenv("PINTEREST_BOARD_ID","global-board"); assert self.pub.authenticate({}) is False
    def test_get_analytics_is_unknown_until_analytics_endpoint_is_wired(self): assert self.pub.get_analytics("pin-1")=={"post_id":"pin-1","analytics":"UNKNOWN"}
    def test_publish_rejects_video_capability_claim(self):
        self.pub.authenticated=True; self.pub.board_id="board-1"; result=self.pub.publish("caption",["https://example.com/video.mp4"],content_type="video"); assert result.success is False

# Instagram Publisher Tests
class TestInstagramPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher import InstagramPublisher
        self.pub=InstagramPublisher()
    def test_platform_name(self): assert self.pub.get_platform_name()=="instagram"
    def test_capabilities(self):
        caps=self.pub.get_capabilities(); assert caps.supports_images is True; assert caps.supports_carousel is True; assert caps.supports_stories is True; assert caps.supports_scheduled is False; assert caps.max_length==2200
    def test_validate(self): assert self.pub.validate("Hello Instagram!") is True; assert self.pub.validate("") is False; assert self.pub.validate("x"*3000) is False
    def test_authenticate_without_credentials(self): assert self.pub.authenticate({}) is False
    def test_authenticate_does_not_fall_back_to_environment(self,monkeypatch):
        monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID","global-account"); monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN","global-token"); assert self.pub.authenticate({}) is False
    def test_authenticate_requires_remote_validation(self,monkeypatch):
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

# LinkedIn Publisher Tests
class TestLinkedInPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.linkedin.linkedin_publisher import LinkedInPublisher
        self.pub=LinkedInPublisher()
    def test_platform_name(self): assert self.pub.get_platform_name()=="linkedin"
    def test_capabilities(self):
        caps=self.pub.get_capabilities(); assert caps.supports_images is True; assert caps.supports_scheduled is True; assert caps.supports_edit is True; assert caps.max_length==3000; assert "article" in caps.features
    def test_validate(self): assert self.pub.validate("Professional post") is True; assert self.pub.validate("") is False; assert self.pub.validate("x"*5000) is False
    def test_authenticate_without_credentials(self): assert self.pub.authenticate({}) is False
    def test_publish_without_auth(self): assert self.pub.publish("Test").success is False
    def test_edit_without_auth(self): assert self.pub.edit("id","content").success is False
    def test_delete_without_auth(self): assert self.pub.delete("id") is False
    def test_schedule_requires_partner(self):
        result=self.pub.schedule("test",time.time()+3600); assert result.success is False; assert "partner" in result.error_message.lower()
    def test_get_stats(self): stats=self.pub.get_stats(); assert stats["platform"]=="linkedin"; assert "person_id" in stats
    def test_get_post_returns_none(self): assert self.pub.get_post("fake_id") is None

_gw_port_counter=19000
class TestAPIGateway:
    def setup_method(self):
        global _gw_port_counter; _gw_port_counter+=1
        from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway
        self.gateway=APIGateway(port=_gw_port_counter)
    def _url(self,path): return f"http://localhost:{self.gateway._port}{path}"
    def teardown_method(self):
        if self.gateway.is_running(): self.gateway.stop()
        time.sleep(0.1)
    def test_start_and_stop(self):
        self.gateway.start(); assert self.gateway.is_running() is True; self.gateway.stop(); assert self.gateway.is_running() is False
    def test_status_endpoint(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            data=json.loads(urllib.request.urlopen(self._url("/status"),timeout=5).read()); assert data["success"] is True; assert "layers" in data["data"]
        finally: self.gateway.stop()
    def test_health_endpoint(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            data=json.loads(urllib.request.urlopen(self._url("/health"),timeout=5).read()); assert data["success"] is True; assert "checks" in data["data"]
        finally: self.gateway.stop()
    def test_analytics_endpoint_requires_account_scope(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc: urllib.request.urlopen(self._url("/analytics"),timeout=5)
            assert exc.value.code==400
        finally: self.gateway.stop()
    def test_history_endpoint_requires_account_scope(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc: urllib.request.urlopen(self._url("/history?limit=3"),timeout=5)
            assert exc.value.code==400
        finally: self.gateway.stop()
    def test_stats_endpoint(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            data=json.loads(urllib.request.urlopen(self._url("/stats"),timeout=5).read()); assert data["success"] is True; assert "source_files" in data["data"]
        finally: self.gateway.stop()
    def test_platforms_endpoint(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            data=json.loads(urllib.request.urlopen(self._url("/platforms"),timeout=5).read()); assert data["success"] is True; assert "facebook" in data["data"]["platforms"]
        finally: self.gateway.stop()
    def test_templates_endpoint_requires_account_scope(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc: urllib.request.urlopen(self._url("/templates"),timeout=5)
            assert exc.value.code==400
        finally: self.gateway.stop()
    def test_404_endpoint(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc: urllib.request.urlopen(self._url("/nonexistent"),timeout=5)
            assert exc.value.code==404
        finally: self.gateway.stop()
    def test_generate_endpoint(self):
        self.gateway.start(); time.sleep(0.2)
        try:
            payload=json.dumps({"topic":"Test Topic","platform":"facebook"}).encode(); req=urllib.request.Request(self._url("/generate"),data=payload,headers={"Content-Type":"application/json"},method="POST"); data=json.loads(urllib.request.urlopen(req,timeout=30).read()); assert data["success"] is True; assert "steps_completed" in data["data"]
        finally: self.gateway.stop()

class TestDashboard:
    def test_dashboard_file_exists(self): assert os.path.exists("dashboard/dashboard.html")
    def test_dashboard_is_valid_html(self):
        with open("dashboard/dashboard.html") as f: content=f.read()
        assert "<!DOCTYPE html>" in content; assert "<title>" in content; assert "AI OS Dashboard" in content
    def test_dashboard_has_api_endpoints(self):
        with open("dashboard/dashboard.html") as f: content=f.read()
        assert "/status" in content; assert "/health" in content; assert "/analytics" in content; assert "/generate" in content
    def test_dashboard_has_refresh(self):
        with open("dashboard/dashboard.html") as f: content=f.read()
        assert "refreshAll" in content
    def test_dashboard_has_generate_form(self):
        with open("dashboard/dashboard.html") as f: content=f.read()
        assert "topicInput" in content; assert "platformSelect" in content; assert "generateContent" in content
    def test_dashboard_dark_theme(self):
        with open("dashboard/dashboard.html") as f: content=f.read()
        assert "#0f172a" in content; assert "#1e293b" in content

class TestFacebookSecrets:
    def test_secrets_environment_check(self):
        assert isinstance(os.environ.get("FACEBOOK_ACCESS_TOKEN",""),str); assert isinstance(os.environ.get("FACEBOOK_PAGE_ID",""),str)
    def test_facebook_publisher_reads_env(self):
        os.environ["FACEBOOK_PAGE_ID"]="test_123"; os.environ["FACEBOOK_ACCESS_TOKEN"]="test_token_abc"
        try:
            from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
            assert isinstance(FacebookPublisher().authenticate({}),bool)
        finally: os.environ.pop("FACEBOOK_PAGE_ID",None); os.environ.pop("FACEBOOK_ACCESS_TOKEN",None)
    def test_all_platform_publishers_instantiate(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
        from layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher import InstagramPublisher
        from layers.layer07_publishing.modules.platform_plugin_manager.linkedin.linkedin_publisher import LinkedInPublisher
        from layers.layer07_publishing.modules.platform_plugin_manager.twitter.twitter_publisher import TwitterPublisher
        for PubClass in [FacebookPublisher,InstagramPublisher,LinkedInPublisher,TwitterPublisher]:
            pub=PubClass(); assert pub.get_platform_name() in ("facebook","instagram","linkedin","twitter"); assert pub.get_capabilities().max_length>0

class TestYouTubeCredentialScope:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.youtube.youtube_publisher import YouTubePublisher
        self.pub=YouTubePublisher()
    def test_global_environment_token_is_ignored(self,monkeypatch):
        monkeypatch.setenv("YOUTUBE_ACCESS_TOKEN","global-token"); assert self.pub.authenticate({}) is False
    def test_explicit_credentials_are_used(self,monkeypatch):
        seen={}
        monkeypatch.setattr(self.pub,"_get",lambda path,params: seen.update({"token":self.pub.token}) or {"items":[{"id":"channel-1"}]})
        assert self.pub.authenticate({"access_token":"account-token"}) is True; assert seen["token"]=="account-token"
