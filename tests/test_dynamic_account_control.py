import tempfile
from pathlib import Path

from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
from layers.layer07_publishing.modules.account_control.decision_engine import DecisionEngine
from layers.layer07_publishing.modules.account_control.policy_registry import PlatformPolicy, PolicyRegistry
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
from layers.layer10_monetization.modules.product_affiliate_selector import ProductAffiliateSelector, ProductCandidate


def test_new_account_is_fully_provisioned_and_isolated():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        registry = AccountRegistry(str(root / "registry.sqlite3"), str(root / "workspaces"))
        registry.register(AccountSpec("yt-tech", "youtube", "ai-tools"))
        registry.register(AccountSpec("yt-travel", "youtube", "travel"))
        first = registry.workspace_path("yt-tech")
        second = registry.workspace_path("yt-travel")
        assert (first / "memory.sqlite3").exists()
        assert (first / "content.sqlite3").exists()
        assert (first / "analytics.sqlite3").exists()
        assert (first / "learning.sqlite3").exists()
        assert first != second
        store = AccountDataStore(registry)
        store.put("yt-tech", "memory", "x", {"value": 1})
        assert store.get("yt-tech", "memory", "x") == {"value": 1}
        assert store.get("yt-travel", "memory", "x") is None


def test_decision_engine_selects_only_enabled_accounts_and_policy():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        registry = AccountRegistry(str(root / "accounts.sqlite3"), str(root / "workspaces"))
        registry.register(AccountSpec("fb-a", "facebook", "fitness", capabilities=["post", "photo"]))
        registry.register(AccountSpec("fb-b", "facebook", "finance", enabled=False))
        policies = PolicyRegistry(str(root / "policies.sqlite3"))
        policies.register(PlatformPolicy("facebook", "2026-01", "config", constraints={"content_types": ["photo", "post"]}))
        decision = DecisionEngine(registry, policies).decide("home workout")
        assert decision.account_id == "fb-a"
        assert decision.platform == "facebook"
        assert decision.niche == "fitness"
        assert decision.policy_version == "2026-01"


def test_repetition_is_account_scoped():
    with tempfile.TemporaryDirectory() as tmp:
        guard = ContentRepetitionGuard(str(Path(tmp) / "history.sqlite3"))
        first = guard.reserve(account_id="a", platform="facebook", content="One post with three points.")
        assert first.allowed
        guard.finalize(first.reservation_id, "post-1")
        same_account = guard.reserve(account_id="a", platform="facebook", content="One post with three points.")
        other_account = guard.reserve(account_id="b", platform="facebook", content="One post with three points.")
        assert not same_account.allowed
        assert other_account.allowed


def test_product_selector_never_invents_unverified_products():
    selector = ProductAffiliateSelector()
    assert selector.select([ProductCandidate("x", "X", "https://example.invalid/x", 1, 1, False)]) is None
    selected = selector.select([ProductCandidate("x", "X", "https://example.invalid/x", 1, .5, True)])
    assert selected["product_id"] == "x"
    assert selected["conversion"] == "UNKNOWN"
    assert selected["sales"] == "UNKNOWN"
