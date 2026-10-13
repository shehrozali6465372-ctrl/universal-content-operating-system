"""Goal-driven product research with review evidence and verified affiliate links.

The agent orchestrates research; provider adapters own data access. It never
fabricates review facts, product URLs, or affiliate tracking parameters.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from layers.layer10_monetization.modules.affiliate_browser import (
    AffiliateBrowserClient,
    AffiliateBrowserGateway,
    AffiliateLink,
    AffiliateProduct,
    AffiliateSearchRequest,
)


@dataclass(frozen=True)
class ProductResearchGoal:
    """Structured, auditable version of a natural-language product goal."""

    title: str
    query: str
    provider: str
    account_ref: str
    marketplace: str = "www.amazon.com"
    audience: str = ""
    target_concerns: tuple[str, ...] = ()
    avoid_claims: tuple[str, ...] = ()
    max_products: int = 8
    min_evidence_confidence: float = 0.65

    def __post_init__(self) -> None:
        for name in ("title", "query", "provider", "account_ref"):
            if not getattr(self, name).strip():
                raise ValueError(name + " is required")
        if not 1 <= self.max_products <= 20:
            raise ValueError("max_products must be between 1 and 20")
        if not 0.0 <= self.min_evidence_confidence <= 1.0:
            raise ValueError("min_evidence_confidence must be between 0 and 1")


@dataclass(frozen=True)
class ReviewEvidence:
    """Review-derived evidence returned by a trusted review research adapter."""

    product_ref: str
    source_urls: tuple[str, ...]
    review_count: int
    average_rating: float | None
    pros: tuple[str, ...] = ()
    cons: tuple[str, ...] = ()
    recurring_complaints: tuple[str, ...] = ()
    ingredient_notes: tuple[str, ...] = ()
    concern_match: float = 0.0
    confidence: float = 0.0
    checked_at: str = ""

    def __post_init__(self) -> None:
        if self.review_count < 0:
            raise ValueError("review_count cannot be negative")
        if self.average_rating is not None and not 0 <= self.average_rating <= 5:
            raise ValueError("average_rating must be between 0 and 5")
        if not 0 <= self.concern_match <= 1 or not 0 <= self.confidence <= 1:
            raise ValueError("concern_match and confidence must be between 0 and 1")


class ProductReviewResearchGateway(Protocol):
    """Collect review evidence from permitted sources/APIs; do not invent data."""

    def research_reviews(
        self, product: AffiliateProduct, goal: ProductResearchGoal
    ) -> ReviewEvidence:
        ...


@dataclass(frozen=True)
class ResearchedProduct:
    product: AffiliateProduct
    review_evidence: ReviewEvidence
    score: float
    affiliate_link: AffiliateLink | None
    link_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": asdict(self.product),
            "reviews": asdict(self.review_evidence),
            "score": round(self.score, 2),
            "affiliate_url": self.affiliate_link.affiliate_url if self.affiliate_link else None,
            "affiliate_source": self.affiliate_link.source if self.affiliate_link else None,
            "affiliate_evidence": dict(self.affiliate_link.evidence) if self.affiliate_link else {},
            "link_error": self.link_error,
        }


@dataclass(frozen=True)
class ProductResearchReport:
    goal: ProductResearchGoal
    status: str
    products: tuple[ResearchedProduct, ...]
    warnings: tuple[str, ...] = ()
    completed_checks: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": asdict(self.goal),
            "status": self.status,
            "products": [p.to_dict() for p in self.products],
            "warnings": list(self.warnings),
            "completed_checks": list(self.completed_checks),
        }


class ProductResearchAgent:
    """Execute search -> review evidence -> rank -> affiliate-link verification."""

    def __init__(
        self,
        browser_gateway: AffiliateBrowserGateway,
        review_gateway: ProductReviewResearchGateway,
    ) -> None:
        self._browser_gateway = browser_gateway
        self._review_gateway = review_gateway

    @staticmethod
    def _score(evidence: ReviewEvidence) -> float:
        # A missing metric contributes zero rather than being guessed.
        rating = (evidence.average_rating or 0.0) / 5.0
        volume = min(evidence.review_count / 1000.0, 1.0)
        coverage = min(len(evidence.source_urls) / 3.0, 1.0)
        complaint_risk = min(
            (len(evidence.recurring_complaints) + len(evidence.cons)) / 8.0, 1.0
        )
        score = (
            25.0 * rating
            + 15.0 * volume
            + 20.0 * coverage
            + 20.0 * evidence.concern_match
            + 20.0 * evidence.confidence
            - 15.0 * complaint_risk
        )
        return max(0.0, min(100.0, score))

    def run(self, goal: ProductResearchGoal) -> ProductResearchReport:
        warnings: list[str] = []
        researched: list[ResearchedProduct] = []
        search = self._browser_gateway.search_products(
            AffiliateSearchRequest(
                provider=goal.provider,
                query=goal.query,
                account_ref=goal.account_ref,
                marketplace=goal.marketplace,
                max_results=goal.max_products,
            )
        )
        AffiliateBrowserClient._validate_search_result(
            AffiliateSearchRequest(
                provider=goal.provider,
                query=goal.query,
                account_ref=goal.account_ref,
                marketplace=goal.marketplace,
                max_results=goal.max_products,
            ),
            search,
        )

        for product in search.products[: goal.max_products]:
            try:
                evidence = self._review_gateway.research_reviews(product, goal)
                if evidence.product_ref != product.product_ref:
                    warnings.append(
                        "Review evidence product mismatch; skipped " + product.product_ref
                    )
                    continue
                if not evidence.source_urls:
                    warnings.append(
                        "No review source URLs; skipped evidence-free product " + product.product_ref
                    )
                    continue
                if evidence.confidence < goal.min_evidence_confidence:
                    warnings.append(
                        "Review evidence confidence below threshold for " + product.product_ref
                    )
                    continue
                score = self._score(evidence)
                affiliate_link = None
                link_error = ""
                try:
                    affiliate_link = self._browser_gateway.create_affiliate_link(
                        account_ref=goal.account_ref, product=product
                    )
                    AffiliateBrowserClient._validate_link(
                        AffiliateSearchRequest(
                            provider=goal.provider,
                            query=goal.query,
                            account_ref=goal.account_ref,
                            marketplace=goal.marketplace,
                            max_results=goal.max_products,
                        ),
                        product,
                        affiliate_link,
                    )
                except Exception as exc:
                    # Preserve useful research, but never pretend the affiliate link exists.
                    link_error = type(exc).__name__ + ": " + str(exc)[:300]
                    warnings.append("Affiliate link not verified for " + product.product_ref)
                researched.append(
                    ResearchedProduct(product, evidence, score, affiliate_link, link_error)
                )
            except Exception as exc:
                warnings.append(
                    "Research failed for " + product.product_ref + " (" + type(exc).__name__ + ")"
                )

        researched.sort(key=lambda item: item.score, reverse=True)
        if not researched:
            status = "incomplete"
        elif any(item.affiliate_link for item in researched):
            status = "completed" if not warnings else "partial"
        else:
            status = "partial"
        checks = ["authenticated product search", "review evidence collected", "products ranked"]
        if any(item.affiliate_link for item in researched):
            checks.append("at least one affiliate link validated against selected product")
        else:
            warnings.append("Goal is not complete: no verified affiliate link was returned.")
        return ProductResearchReport(
            goal=goal,
            status=status,
            products=tuple(researched),
            warnings=tuple(warnings),
            completed_checks=tuple(checks),
        )


__all__ = [
    "ProductResearchAgent",
    "ProductResearchGoal",
    "ProductResearchReport",
    "ProductReviewResearchGateway",
    "ResearchedProduct",
    "ReviewEvidence",
]
