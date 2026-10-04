from layers.layer10_monetization.modules.affiliate_browser import (
    AffiliateBrowserClient, AffiliateSearchRequest,
)
from layers.layer14_enterprise_integration.modules.affiliate_browser_gateway import (
    PersonalBrowserAffiliateGateway,
)


def test_personal_browser_gateway_search_and_sitestripe_link():
    calls = []

    def fake_request(method, path, payload=None, timeout=75.0):
        calls.append((method, path, payload))
        actions = payload["actions"]
        if payload["url"].endswith("/s?k=coffee+maker"):
            return 200, {"result": {
                "links": [
                    {"text": "Coffee Maker", "href": "https://www.amazon.com/dp/B000000001"},
                    {"text": "duplicate", "href": "https://www.amazon.com/dp/B000000001"},
                ],
                "persistent_profile": True,
            }}
        return 200, {"result": {
            "links": [
                {"text": "tagged", "href": "https://www.amazon.com/dp/B000000001?tag=example-20"},
            ],
            "text": "",
            "final_url": payload["url"],
            "persistent_profile": True,
        }}

    gateway = PersonalBrowserAffiliateGateway(fake_request)
    link = AffiliateBrowserClient(gateway).search_and_get_link(
        AffiliateSearchRequest(
            provider="amazon",
            query="coffee maker",
            account_ref="amazon-primary",
        )
    )

    assert link.product_ref == "B000000001"
    assert link.affiliate_url.endswith("tag=example-20")
    assert link.source == "authenticated_browser"
    assert link.evidence["method"] == "amazon_sitestripe"
    assert link.evidence["product_url"].endswith("/B000000001")
    assert calls[0][2]["profile_ref"] == "amazon-primary"


def test_personal_browser_gateway_does_not_accept_untagged_link():
    def fake_request(method, path, payload=None, timeout=75.0):
        return 200, {"result": {
            "links": [{"text": "product", "href": "https://www.amazon.com/dp/B000000001"}],
            "text": "",
            "final_url": payload["url"],
            "persistent_profile": True,
        }}

    gateway = PersonalBrowserAffiliateGateway(fake_request)
    try:
        AffiliateBrowserClient(gateway).search_and_get_link(
            AffiliateSearchRequest(
                provider="amazon",
                query="coffee maker",
                account_ref="amazon-primary",
            )
        )
    except RuntimeError:
        return
    raise AssertionError("untagged Amazon URL must fail closed")
