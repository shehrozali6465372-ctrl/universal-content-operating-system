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
