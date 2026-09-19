from layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane import ControlPlane


def test_control_plane_owns_meta_account_sync(monkeypatch):
    class FakeDiscovery:
        def __init__(self):
            pass

        def provision(self, registry, *, default_niche):
            assert default_niche == "fitness"
            return {"facebook_discovered": 12, "instagram_discovered": 11, "provisioned": []}

    monkeypatch.setattr(
        "layers.layer07_publishing.modules.account_control.meta_asset_discovery.MetaAssetDiscovery",
        FakeDiscovery,
    )
    result = ControlPlane().sync_meta_accounts(default_niche="fitness")
    assert result["facebook_discovered"] == 12
    assert result["instagram_discovered"] == 11
