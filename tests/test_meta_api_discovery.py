from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway


def test_meta_discovery_endpoint_uses_runtime_token_and_provisions(monkeypatch):
    monkeypatch.setenv("META_ACCESS_TOKEN", "test-only-token")

    class FakeDiscovery:
        def __init__(self):
            pass

        def provision(self, registry, *, default_niche):
            assert default_niche == "general"
            return {
                "facebook_discovered": 12,
                "instagram_discovered": 11,
                "provisioned": [],
            }

    monkeypatch.setattr(
        "layers.layer07_publishing.modules.account_control.meta_asset_discovery.MetaAssetDiscovery",
        FakeDiscovery,
    )

    response = APIGateway()._handle_meta_discover({})
    assert response.status_code == 200
    assert response.error == ""
    assert response.data["facebook_discovered"] == 12
    assert response.data["instagram_discovered"] == 11
