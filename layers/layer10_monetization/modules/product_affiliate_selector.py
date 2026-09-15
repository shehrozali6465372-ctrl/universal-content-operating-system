"""Evidence-based product/affiliate selection facade.

The selector only chooses from caller-supplied, verified product records. It never
fabricates ASINs, URLs, prices, commission rates, conversions, or sales.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ProductCandidate:
    product_id: str
    title: str
    url: str
    relevance: float = 0.0
    intent_match: float = 0.0
    verified: bool = False
    metadata: Dict[str, Any] = None

    def score(self) -> float:
        return max(0.0, float(self.relevance)) * 0.6 + max(0.0, float(self.intent_match)) * 0.4


class ProductAffiliateSelector:
    def select(self, candidates: Iterable[ProductCandidate], *, require_verified: bool = True) -> Optional[Dict[str, Any]]:
        valid: List[ProductCandidate] = []
        for candidate in candidates:
            if not candidate.product_id or not candidate.url or not candidate.title:
                continue
            if require_verified and not candidate.verified:
                continue
            valid.append(candidate)
        if not valid:
            return None
        selected = max(valid, key=lambda item: (item.score(), item.product_id))
        return {
            "product_id": selected.product_id,
            "title": selected.title,
            "url": selected.url,
            "selection_score": selected.score(),
            "evidence": "verified_candidate" if selected.verified else "candidate",
            "metadata": selected.metadata or {},
            "conversion": "UNKNOWN",
            "sales": "UNKNOWN",
        }
