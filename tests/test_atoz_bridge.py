import uuid

import pytest

from layers.layer23_website_manager.integration.atoz_bridge import dispatch_job


def test_atoz_bridge_requires_real_site_identity():
    payload = {
        "request_id": str(uuid.uuid4()),
        "niche_id": str(uuid.uuid4()),
        "job_type": "content",
        "context": {"title": "Real title", "content": "Real body"},
    }
    with pytest.raises(ValueError, match="domain and context.site_name"):
        dispatch_job(payload)


def test_atoz_bridge_rejects_unknown_job_type():
    payload = {
        "request_id": str(uuid.uuid4()),
        "niche_id": str(uuid.uuid4()),
        "job_type": "unknown",
        "context": {"domain": "example.test", "site_name": "AtoZ Product Hub"},
    }
    with pytest.raises(ValueError, match="unsupported job_type"):
        dispatch_job(payload)


def test_atoz_pinterest_assets_requires_real_publish_inputs(monkeypatch):
    class FakePin:
        pin_id = "pin-1"
        def to_dict(self):
            return {"pin_id": self.pin_id, "status": "draft"}

    class FakeManager:
        def create_pin(self, **kwargs):
            assert kwargs["account_id"] == "pinterest:1"
            return FakePin()

    import layers.layer23_website_manager.integration.atoz_bridge as bridge
    monkeypatch.setattr(bridge, "get_pin_manager", lambda: FakeManager())

    payload = {
        "request_id": str(uuid.uuid4()),
        "niche_id": str(uuid.uuid4()),
        "job_type": "pinterest_assets",
        "context": {
            "domain": "atoz.example",
            "site_name": "AtoZ Product Hub",
            "title": "Real pin",
            "website_url": "https://atoz.example/article",
            "account_id": "pinterest:1",
            "board_id": "board-1",
            "image_path": "/tmp/real-image.png",
        },
    }
    result = dispatch_job(payload)
    assert result["published"] is False
    assert result["result_ref"] == "layer23:pinterest-pin:pin-1"
