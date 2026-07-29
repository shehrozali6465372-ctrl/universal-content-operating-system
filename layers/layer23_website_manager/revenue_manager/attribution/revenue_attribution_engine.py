"""RevenueAttributionEngine — Map visitor → pin → board → article → product → revenue."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RevenueAttributionEngine:
    def __init__(self):
        self._attributions: List[Dict] = []

    def attribute(self, visitor_id: str = "", pin_id: str = "", board_id: str = "",
                   article_id: str = "", product_id: str = "", merchant: str = "",
                   sale_amount: float = 0.0, commission: float = 0.0) -> Dict[str, Any]:
        chain = {"visitor_id": visitor_id, "pin_id": pin_id, "board_id": board_id,
                  "article_id": article_id, "product_id": product_id, "merchant": merchant,
                  "sale_amount": sale_amount, "commission": commission}
        chain["attribution_path"] = " → ".join(filter(None, [f"Pin({pin_id})" if pin_id else "",
            f"Board({board_id})" if board_id else "", f"Article({article_id})" if article_id else "",
            f"Product({product_id})" if product_id else "", "Sale"]))
        self._attributions.append(chain)
        return chain

    def get_stats(self) -> Dict: return {"total_attributions": len(self._attributions)}
