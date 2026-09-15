import sqlite3
import tempfile
from pathlib import Path

from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
from layers.layer07_publishing.modules.account_control.decision_engine import DecisionEngine
from layers.layer07_publishing.modules.account_control.policy_registry import PlatformPolicy, PolicyRegistry
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
from layers.layer10_monetization.modules.product_affiliate_selector import ProductAffiliateSelector, ProductCandidate
from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import ContentRequest, ContentResponse
import layers.layer14_enterprise_integration.modules.master_orchestrator.production_pipeline as production_pipeline


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


def test_account_local_append_preserves_events_and_isolation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        registry = AccountRegistry(str(root / "accounts.sqlite3"), str(root / "workspaces"))
        registry.register(AccountSpec("a", "facebook", "fitness"))
        registry.register(AccountSpec("b", "facebook", "finance"))
        store = AccountDataStore(registry)
        store.append("a", "learning", "execution_outcomes", {"id": 1})
        store.append("a", "learning", "execution_outcomes", {"id": 2})
        store.append("b", "learning", "execution_outcomes", {"id": 3})
        assert store.get("a", "learning", "collection:execution_outcomes") == [{"id": 1}, {"id": 2}]
        assert store.get("b", "learning", "collection:execution_outcomes") == [{"id": 3}]


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


def test_repetition_guard_migrates_legacy_schema_without_status():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "legacy.sqlite3"
        with sqlite3.connect(db_path) as db:
            db.execute("""CREATE TABLE content_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content_fingerprint TEXT NOT NULL,
                template_fingerprint TEXT NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(account_id, content_fingerprint),
                UNIQUE(account_id, template_fingerprint)
            )""")
            content_fp, template_fp = ContentRepetitionGuard.fingerprints("Legacy post.")
            db.execute("INSERT INTO content_history (account_id,platform,content_fingerprint,template_fingerprint,created_at) VALUES (?,?,?,?,?)", ("legacy", "facebook", content_fp, template_fp, 1.0))
        guard = ContentRepetitionGuard(str(db_path))
        duplicate = guard.reserve(account_id="legacy", platform="facebook", content="Legacy post.")
        assert not duplicate.allowed
        assert duplicate.reason == "exact_content_repeat"
        pending = guard.pending("legacy")
        assert pending == []
        with sqlite3.connect(db_path) as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(content_history)")}
            assert {"status", "post_id"}.issubset(columns)


def test_product_selector_never_invents_unverified_products():
    selector = ProductAffiliateSelector()
    assert selector.select([ProductCandidate("x", "X", "https://example.invalid/x", 1, 1, False)]) is None
    selected = selector.select([ProductCandidate("x", "X", "https://example.invalid/x", 1, .5, True)])
    assert selected["product_id"] == "x"
    assert selected["conversion"] == "UNKNOWN"
    assert selected["sales"] == "UNKNOWN"


def test_production_pipeline_rejects_credentials_from_another_account(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        registry = AccountRegistry(str(root / "accounts.sqlite3"), str(root / "workspaces"))
        registry.register(AccountSpec("account-a", "facebook", "fitness", credentials_ref="account_a"))
        monkeypatch.setattr(production_pipeline, "AccountRegistry", lambda: registry)
        req = ContentRequest("secure publishing test", platform="facebook", include_image=False)
        req.metadata.update({"account_id": "account-a", "credentials_ref": "account_b", "content_type": "post"})
        response = ContentResponse(req)
        response.text = "A real account-scoped publishing test."
        try:
            production_pipeline.ProductionPipeline()._publish(req, response, {})
        except RuntimeError as exc:
            assert "credentials_ref does not belong" in str(exc)
        else:
            raise AssertionError("cross-account credentials_ref was accepted")
