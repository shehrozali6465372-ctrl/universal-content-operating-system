import json
from layers.layer07_publishing.modules.account_control.credential_resolver import AccountCredentialResolver


def test_credential_reference_resolves_only_its_own_secret(monkeypatch):
    monkeypatch.setenv("UCOS_CREDENTIALS_ACCOUNT_A", json.dumps({"access_token":"token-a"}))
    monkeypatch.setenv("UCOS_CREDENTIALS_ACCOUNT_B", json.dumps({"access_token":"token-b"}))
    assert AccountCredentialResolver.resolve("account_a")["access_token"] == "token-a"
    assert AccountCredentialResolver.resolve("account_b")["access_token"] == "token-b"
    assert AccountCredentialResolver.resolve("missing") == {}
