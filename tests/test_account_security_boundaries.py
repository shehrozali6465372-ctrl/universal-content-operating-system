import json
import os
import tempfile
import urllib.request

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway


def test_account_workspace_ids_cannot_collide_after_sanitization():
    with tempfile.TemporaryDirectory() as td:
        registry = AccountRegistry(os.path.join(td, "registry.sqlite3"), os.path.join(td, "workspaces"))
        a = registry.register(AccountSpec("food/a", "instagram", "food"))
        b = registry.register(AccountSpec("food?a", "instagram", "food"))
        assert a != b
        assert (a / "account.json").exists()
        assert (b / "account.json").exists()
        assert json.loads((a / "account.json").read_text())["account_id"] == "food/a"
        assert json.loads((b / "account.json").read_text())["account_id"] == "food?a"


def test_remote_gateway_requires_token():
    gateway = APIGateway(host="0.0.0.0", port=0)
    old = os.environ.pop("UCOS_API_TOKEN", None)
    try:
        assert gateway._requires_auth()
        assert not gateway._authorized({"Authorization": "Bearer anything"})
        os.environ["UCOS_API_TOKEN"] = "secret-token"
        assert gateway._authorized({"Authorization": "Bearer secret-token"})
        assert not gateway._authorized({"Authorization": "Bearer wrong"})
    finally:
        if old is None:
            os.environ.pop("UCOS_API_TOKEN", None)
        else:
            os.environ["UCOS_API_TOKEN"] = old


def test_local_gateway_does_not_require_token():
    gateway = APIGateway(host="127.0.0.1", port=0)
    assert not gateway._requires_auth()
    assert gateway._authorized({})
