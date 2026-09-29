from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway


def test_browser_task_requires_url():
    gateway = APIGateway()
    response = gateway._handle_browser_task({})
    assert response.status_code == 400


def test_browser_task_dispatch_contract(monkeypatch):
    gateway = APIGateway()

    def fake_request(method, path, payload=None, timeout=75.0):
        assert method == "POST"
        assert path == "/execute"
        assert payload["url"] == "https://example.com"
        return 200, {"state": "completed", "result": {"title": "Example Domain"}}

    monkeypatch.setattr(gateway, "_browser_request", fake_request)
    response = gateway._handle_browser_task({"url": "https://example.com"})
    assert response.status_code == 202
    assert response.data["source"] == "ucos_personal_browser"
    assert response.data["result"]["title"] == "Example Domain"


def test_public_healthz_contract():
    gateway = APIGateway()
    response = gateway._handle_healthz({})
    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert response.data["layers"] == 23
