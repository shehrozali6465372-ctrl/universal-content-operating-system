"""Regression tests for goal-driven product research and evidence gates."""
from layers.layer02_research.modules.niche_intelligence.product_research_agent import (
    ProductResearchAgent,
    ProductResearchGoal,
    ReviewEvidence,
)
from layers.layer10_monetization.modules.affiliate_browser import (
    AffiliateLink,
    AffiliateProduct,
    AffiliateSearchResult,
)


class FakeBrowser:
    def __init__(self, products):
        self.products = products
        self.link_calls = []

    def search_products(self, request):
        return AffiliateSearchResult(
            provider=request.provider,
            account_ref=request.account_ref,
            products=tuple(self.products),
            source="authenticated_browser",
        )

    def create_affiliate_link(self, *, account_ref, product):
        self.link_calls.append(product.product_ref)
        return AffiliateLink(
            provider="amazon",
            account_ref=account_ref,
            product_ref=product.product_ref,
            affiliate_url="https://www.amazon.com/dp/B000000001?tag=validtag-20",
            source="authenticated_browser",
            evidence={"site_stripe": True, "product_ref": product.product_ref},
        )


class FakeReviews:
    def __init__(self, evidence_by_ref):
        self.evidence_by_ref = evidence_by_ref

    def research_reviews(self, product, goal):
        return self.evidence_by_ref[product.product_ref]


def goal(**kwargs):
    values = {
        "title": "Find useful skincare products and verified affiliate links",
        "query": "skincare for sensitive skin",
        "provider": "amazon",
        "account_ref": "amazon-primary",
        "target_concerns": ("sensitive skin",),
        "max_products": 5,
    }
    values.update(kwargs)
    return ProductResearchGoal(**values)


def product(ref, title):
    return AffiliateProduct(
        product_ref=ref,
        title=title,
        product_url="https://www.amazon.com/dp/" + ref,
        price="$15.00",
        currency="USD",
    )


def evidence(ref, **kwargs):
    values = {
        "product_ref": ref,
        "source_urls": ("https://reviews.example/source-a", "https://reviews.example/source-b"),
        "review_count": 450,
        "average_rating": 4.4,
        "pros": ("lightweight",),
        "cons": ("fragrance may bother some users",),
        "recurring_complaints": ("scent sensitivity",),
        "ingredient_notes": ("contains fragrance",),
        "concern_match": 0.8,
        "confidence": 0.9,
        "checked_at": "2026-10-14T00:00:00Z",
    }
    values.update(kwargs)
    return ReviewEvidence(**values)


def test_goal_runs_search_reviews_rank_and_validates_affiliate_link():
    p1 = product("B000000001", "Fragranced moisturizer")
    p2 = product("B000000002", "Gentle moisturizer")
    browser = FakeBrowser([p1, p2])
    reviews = FakeReviews({
        p1.product_ref: evidence(p1.product_ref, concern_match=0.3, confidence=0.8),
        p2.product_ref: evidence(
            p2.product_ref, average_rating=4.7, concern_match=0.95,
            recurring_complaints=(), cons=(), confidence=0.98,
        ),
    })

    report = ProductResearchAgent(browser, reviews).run(goal())

    assert report.status == "completed"
    assert report.products[0].product.product_ref == p2.product_ref
    assert report.products[0].affiliate_link is not None
    assert report.products[0].affiliate_link.product_ref == p2.product_ref
    assert report.products[0].affiliate_link.affiliate_url.endswith("tag=validtag-20")
    assert set(browser.link_calls) == {p1.product_ref, p2.product_ref}
    assert "products ranked" in report.completed_checks


def test_product_without_review_sources_is_not_recommended_or_linked():
    p = product("B000000003", "No-evidence product")
    browser = FakeBrowser([p])
    reviews = FakeReviews({
        p.product_ref: evidence(p.product_ref, source_urls=()),
    })

    report = ProductResearchAgent(browser, reviews).run(goal())

    assert report.status == "incomplete"
    assert report.products == ()
    assert browser.link_calls == []
    assert any("No review source URLs" in warning for warning in report.warnings)


def test_low_confidence_review_evidence_is_rejected():
    p = product("B000000004", "Unverified product")
    browser = FakeBrowser([p])
    reviews = FakeReviews({
        p.product_ref: evidence(p.product_ref, confidence=0.2),
    })

    report = ProductResearchAgent(browser, reviews).run(goal(min_evidence_confidence=0.7))

    assert report.status == "incomplete"
    assert not report.products
    assert not browser.link_calls


def test_wrong_product_review_evidence_is_rejected():
    p = product("B000000005", "Product A")
    browser = FakeBrowser([p])
    reviews = FakeReviews({
        p.product_ref: evidence("DIFFERENT_PRODUCT"),
    })

    report = ProductResearchAgent(browser, reviews).run(goal())

    assert report.status == "incomplete"
    assert not report.products
    assert any("product mismatch" in warning for warning in report.warnings)


def test_link_failure_does_not_get_reported_as_success():
    p = product("B000000006", "Product with link failure")

    class BrokenLinkBrowser(FakeBrowser):
        def create_affiliate_link(self, *, account_ref, product):
            raise RuntimeError("affiliate session unavailable")

    browser = BrokenLinkBrowser([p])
    reviews = FakeReviews({p.product_ref: evidence(p.product_ref)})

    report = ProductResearchAgent(browser, reviews).run(goal())

    assert report.status == "partial"
    assert report.products[0].affiliate_link is None
    assert report.products[0].link_error.startswith("RuntimeError")
    assert any("no verified affiliate link" in warning for warning in report.warnings)
