from layers.layer10_monetization.modules.affiliate_browser import (
    AffiliateBrowserClient,
    AffiliateLink,
    AffiliateProduct,
    AffiliateSearchRequest,
    AffiliateSearchResult,
    BrowserAffiliateError,
)


class FakeGateway:
    def __init__(self, source="authenticated_browser"):
        self.source = source

    def search_products(self, request):
        return AffiliateSearchResult(
            provider=request.provider,
            account_ref=request.account_ref,
            products=(
                AffiliateProduct(
                    product_ref="p-1",
                    title="Example Product",
                    product_url="https://shop.example/product/p-1",
                ),
            ),
            source=self.source,
        )

    def create_affiliate_link(self, *, account_ref, product):
        return AffiliateLink(
            provider="amazon",
            account_ref=account_ref,
            product_ref=product.product_ref,
            affiliate_url="https://shop.example/ref/p-1?tag=real",
            source=self.source,
            evidence={"page_url": product.product_url, "method": "browser"},
        )


def test_search_and_get_link_requires_real_browser_provenance():
    request = AffiliateSearchRequest(provider="amazon", query="coffee maker", account_ref="acct-1")
    link = AffiliateBrowserClient(FakeGateway()).search_and_get_link(request)
    assert link.affiliate_url.startswith("https://")
    assert link.account_ref == "acct-1"
    assert link.product_ref == "p-1"
    assert link.evidence["method"] == "browser"


def test_fabricated_source_is_rejected():
    request = AffiliateSearchRequest(provider="amazon", query="coffee maker", account_ref="acct-1")
    try:
        AffiliateBrowserClient(FakeGateway(source="synthetic")).search_and_get_link(request)
    except BrowserAffiliateError:
        return
    raise AssertionError("synthetic affiliate provenance must fail closed")


def test_http_affiliate_url_is_rejected():
    class BadGateway(FakeGateway):
        def create_affiliate_link(self, *, account_ref, product):
            return AffiliateLink(
                provider="amazon",
                account_ref=account_ref,
                product_ref=product.product_ref,
                affiliate_url="http://shop.example/ref/p-1",
                source="authenticated_browser",
                evidence={"page_url": product.product_url},
            )

    request = AffiliateSearchRequest(provider="amazon", query="coffee maker", account_ref="acct-1")
    try:
        AffiliateBrowserClient(BadGateway()).search_and_get_link(request)
    except BrowserAffiliateError:
        return
    raise AssertionError("non-HTTPS affiliate URL must fail closed")
