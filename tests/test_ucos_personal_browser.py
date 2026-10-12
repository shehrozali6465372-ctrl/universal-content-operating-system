import pytest

from services.ucos_browser.server import (
    _AFFILIATE_CLIPBOARD_CAPTURE_SCRIPT,
    _is_amazon_affiliate_link,
    validate_url,
)


def test_public_https_url_allowed():
    assert validate_url("https://example.com/path") == "https://example.com/path"

def test_clipboard_capture_script_intercepts_site_stripe_copy_in_chromium():
    from playwright.sync_api import sync_playwright

    affiliate_url = "https://www.amazon.com/dp/B012345678?tag=ci-store-20&linkCode=ogi"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = browser.new_page()
            page.add_init_script(_AFFILIATE_CLIPBOARD_CAPTURE_SCRIPT)
            page.goto("data:text/html,<html><body><input id='link' value='test'></body></html>")
            page.evaluate(
                """async url => {
                    await navigator.clipboard.writeText(url);
                    return window.__ucosAffiliateClipboardState?.text || '';
                }""",
                affiliate_url,
            )
            captured = page.evaluate("window.__ucosAffiliateClipboardState.text")
            assert captured == affiliate_url
        finally:
            browser.close()


def test_affiliate_link_validator_preserves_only_real_amazon_affiliate_urls():
    tagged = "https://www.amazon.com/dp/B012345678?tag=my-store-20&linkCode=ogi"
    short = "https://amzn.to/abc123"
    assert _is_amazon_affiliate_link(tagged)
    assert _is_amazon_affiliate_link(short)
    assert not _is_amazon_affiliate_link("https://www.amazon.com/dp/B012345678")
    assert not _is_amazon_affiliate_link("https://amazon.com.attacker.example/dp/B012345678?tag=x-20")
    assert not _is_amazon_affiliate_link("http://www.amazon.com/dp/B012345678?tag=my-store-20")
    assert not _is_amazon_affiliate_link("https://example.com/?tag=my-store-20")


def test_affiliate_link_action_returns_exact_site_stripe_url(monkeypatch):
    url = "https://www.amazon.com/dp/B012345678?tag=my-store-20&linkCode=ogi&th=1"

    class AffiliatePage(_FakeBrowserPage):
        def evaluate(self, script):
            if "__ucosAffiliateClipboardState" in script:
                return [url]
            return dict(self.focused)

    page = AffiliatePage()
    server = _patch_fake_browser(monkeypatch, page)
    result = server.execute_task({
        "profile_ref": "amazon-primary",
        "url": "https://www.amazon.com/",
        "actions": [{"type": "affiliate_link"}],
    })
    assert result["affiliate_link"] == url
    assert result["events"] == [{"type": "affiliate_link_captured"}]


def test_affiliate_link_action_rejects_plain_product_url(monkeypatch):
    class PlainProductPage(_FakeBrowserPage):
        def evaluate(self, script):
            if "__ucosAffiliateClipboardState" in script:
                return ["https://www.amazon.com/dp/B012345678"]
            return dict(self.focused)

    page = PlainProductPage()
    server = _patch_fake_browser(monkeypatch, page)
    with pytest.raises(ValueError, match="No Amazon affiliate link detected"):
        server.execute_task({
            "profile_ref": "amazon-primary",
            "url": "https://www.amazon.com/",
            "actions": [{"type": "affiliate_link"}],
        })



def test_non_http_scheme_rejected():
    with pytest.raises(ValueError):
        validate_url("file:///etc/passwd")


def test_localhost_rejected():
    with pytest.raises(ValueError):
        validate_url("http://localhost:8000/health")


def test_private_ipv4_rejected():
    with pytest.raises(ValueError):
        validate_url("http://127.0.0.1:8000/")


def test_profile_ref_is_safely_scoped():
    from services.ucos_browser.server import _profile_ref
    assert _profile_ref("amazon-primary") == "amazon-primary"
    assert "/" not in _profile_ref("amazon/primary")


def test_profile_ref_rejects_empty():
    from services.ucos_browser.server import _profile_ref
    with pytest.raises(ValueError):
        _profile_ref("")



class _FakeBrowserMouse:
    def __init__(self):
        self.calls = []

    def click(self, x, y):
        self.calls.append(("click", x, y))

    def wheel(self, delta_x, delta_y):
        self.calls.append(("wheel", delta_x, delta_y))


class _FakeBrowserKeyboard:
    def __init__(self):
        self.calls = []

    def insert_text(self, value):
        self.calls.append(("insert_text", value))

    def press(self, key):
        self.calls.append(("press", key))


class _FakeBrowserPage:
    url = "https://example.com/"
    viewport_size = {"width": 640, "height": 480}

    def __init__(self):
        self.mouse = _FakeBrowserMouse()
        self.keyboard = _FakeBrowserKeyboard()
        self.focused = {
            "editable": True,
            "tag": "input",
            "type": "text",
            "password": False,
            "placeholder": "Search",
            "label": "q",
        }

    def evaluate(self, _script):
        return dict(self.focused)

    def wait_for_timeout(self, _ms):
        return None

    def screenshot(self, **_kwargs):
        return b"png"

    def set_default_timeout(self, _timeout):
        return None


def _patch_fake_browser(monkeypatch, page):
    from services.ucos_browser import server

    runtime = {
        "page": page,
        "last_used": 0,
        "state_store_enabled": False,
        "disk_persistent": False,
        "persistent_profile": True,
        "profile_persistence_backend": "neon_postgres",
    }
    monkeypatch.setattr(server, "_get_browser_runtime", lambda *_args: (runtime, False))
    monkeypatch.setattr(server, "_assert_public_page", lambda _page: None)
    return server


def test_screen_click_uses_validated_viewport_coordinates(monkeypatch):
    page = _FakeBrowserPage()
    server = _patch_fake_browser(monkeypatch, page)

    result = server.execute_task({
        "profile_ref": "amazon-primary",
        "url": "https://example.com/",
        "actions": [
            {"type": "click_at", "x": 120, "y": 80},
            {"type": "screenshot"},
        ],
    })

    assert page.mouse.calls == [("click", 120, 80)]
    assert result["viewport"] == {"width": 640, "height": 480}
    assert result["focused"]["editable"] is True
    assert result["screenshot"] == b"png".hex()


def test_screen_click_rejects_coordinates_outside_viewport(monkeypatch):
    page = _FakeBrowserPage()
    server = _patch_fake_browser(monkeypatch, page)

    with pytest.raises(ValueError, match="within the 640x480 viewport"):
        server.execute_task({
            "profile_ref": "amazon-primary",
            "url": "https://example.com/",
            "actions": [{"type": "click_at", "x": 640, "y": 10}],
        })


def test_screen_interactions_scroll_type_and_press(monkeypatch):
    page = _FakeBrowserPage()
    server = _patch_fake_browser(monkeypatch, page)

    result = server.execute_task({
        "profile_ref": "amazon-primary",
        "url": "https://example.com/",
        "actions": [
            {"type": "scroll", "delta_x": 0, "delta_y": 250},
            {"type": "type_text", "text": "search terms"},
            {"type": "press_key", "key": "Enter"},
        ],
    })

    assert page.mouse.calls == [("wheel", 0, 250)]
    assert page.keyboard.calls == [("insert_text", "search terms"), ("press", "Enter")]
    assert [event["type"] for event in result["events"]] == ["scroll", "type_text", "press_key"]
    assert result["events"][1]["length"] == len("search terms")



def test_navigation_during_focus_read_does_not_fail_click(monkeypatch):
    class NavigatingPage(_FakeBrowserPage):
        def evaluate(self, _script):
            raise RuntimeError(
                "Execution context was destroyed, most likely because of a navigation"
            )

    page = NavigatingPage()
    server = _patch_fake_browser(monkeypatch, page)

    result = server.execute_task({
        "profile_ref": "amazon-primary",
        "url": "https://example.com/",
        "actions": [
            {"type": "click_at", "x": 200, "y": 120},
            {"type": "screenshot"},
        ],
    })

    # The actual click and screenshot must still succeed even if optional focus
    # metadata cannot be read during a page navigation.
    assert page.mouse.calls == [("click", 200, 120)]
    assert result["events"][0]["type"] == "click_at"
    assert result["focused"]["editable"] is False
    assert result["focused"]["unavailable"] is True
    assert result["screenshot"] == b"png".hex()
