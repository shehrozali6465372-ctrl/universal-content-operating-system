"""AutoLinkInserter — Automatically insert affiliate links into content at optimal positions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.exceptions import InsertionError


class AutoLinkInserter:
    """Insert affiliate links into articles at optimal positions for maximum CTR."""

    def __init__(self) -> None:
        self._insertion_log: List[dict] = []

    def insert_link(self, content: str, affiliate_url: str,
                     anchor_text: str = "",
                     position: str = "after_first_paragraph") -> Dict[str, Any]:
        """Insert an affiliate link at the optimal position in content."""
        if not content:
            raise InsertionError("Content is empty")
        if not affiliate_url:
            raise InsertionError("Affiliate URL is empty")

        html_link = f'<a href="{affiliate_url}" rel="nofollow sponsored">{anchor_text or "Check Price"}</a>'
        modified_content = content
        insert_position = 0

        if position == "after_first_paragraph":
            paragraphs = content.split("\n\n")
            if len(paragraphs) > 1:
                first = paragraphs[0]
                rest = "\n\n".join(paragraphs[1:])
                modified_content = f"{first}\n\n{html_link}\n\n{rest}"
                insert_position = len(first)
            else:
                modified_content = f"{content}\n\n{html_link}"

        elif position == "before_conclusion":
            modified_content = f"{content}\n\n{html_link}"

        elif position == "middle":
            mid = len(content) // 2
            modified_content = content[:mid] + f"\n\n{html_link}\n\n" + content[mid:]

        result = {
            "original_length": len(content),
            "modified_length": len(modified_content),
            "insert_position": insert_position,
            "html_link": html_link,
            "modified_content": modified_content,
            "position_used": position,
        }

        self._insertion_log.append(result)
        return result

    def insert_multiple(self, content: str, links: List[Dict[str, str]]) -> Dict[str, Any]:
        """Insert multiple affiliate links at different positions."""
        modified = content
        insertions = []

        for i, link_info in enumerate(links):
            try:
                positions = ["after_first_paragraph", "middle", "before_conclusion"]
                pos = positions[i % len(positions)]
                result = self.insert_link(modified, link_info["url"],
                                           link_info.get("text", ""), pos)
                modified = result["modified_content"]
                insertions.append({"link": link_info["url"], "position": pos})
            except Exception as e:
                insertions.append({"link": link_info["url"], "error": str(e)})

        result = {
            "total_insertions": len(links),
            "successful": sum(1 for ins in insertions if "error" not in ins),
            "modified_content": modified,
        }
        self._insertion_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_insertions": len(self._insertion_log)}
