"""AttributionEngine — AI-powered traffic attribution: visitor → source → pin → board → article."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.traffic_manager.exceptions import AttributionError


class AttributionEngine:
    """Attribute traffic to the correct source, content, and marketing touchpoint."""

    def __init__(self) -> None:
        self._attribution_log: List[dict] = []

    def attribute_traffic(self, source_type: str, article_id: str = "",
                           pin_id: str = "", board_id: str = "",
                           account_id: str = "") -> Dict[str, Any]:
        """Attribute a visit to its source chain."""
        chain = {"visitor": {}, "source": source_type, "article_id": article_id}
        if pin_id: chain["pin_id"] = pin_id
        if board_id: chain["board_id"] = board_id
        if account_id: chain["account_id"] = account_id

        if source_type == "pinterest":
            if pin_id and board_id:
                chain["attribution_path"] = f"Pin({pin_id}) → Board({board_id}) → Article({article_id})"
                chain["confidence"] = 0.9
            else:
                chain["attribution_path"] = f"Pinterest → Article({article_id})"
                chain["confidence"] = 0.6
        elif source_type == "google_organic":
            chain["attribution_path"] = f"Google Search → Article({article_id})"
            chain["confidence"] = 0.8
        else:
            chain["attribution_path"] = f"{source_type.replace('_', ' ').title()} → Article({article_id})"
            chain["confidence"] = 0.5

        self._attribution_log.append(chain)
        return chain

    def get_stats(self) -> Dict[str, Any]:
        return {"total_attributions": len(self._attribution_log)}
