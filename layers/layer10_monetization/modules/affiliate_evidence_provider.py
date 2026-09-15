"""Real-time affiliate evidence provider.

UCOS does not invent products. Configure UCOS_AFFILIATE_SEARCH_URL to an approved
affiliate/catalog service that returns a JSON array of verified candidates.
"""
from __future__ import annotations
import json, os, urllib.parse, urllib.request, urllib.error
from typing import Any, Dict, List
from layers.layer10_monetization.modules.product_affiliate_selector import ProductAffiliateSelector, ProductCandidate

class AffiliateEvidenceProvider:
    def search(self, topic: str, niche: str, platform: str) -> List[ProductCandidate]:
        endpoint=os.environ.get("UCOS_AFFILIATE_SEARCH_URL","").strip()
        if not endpoint: return []
        params=urllib.parse.urlencode({"q":topic,"niche":niche,"platform":platform})
        req=urllib.request.Request(endpoint+(("&" if "?" in endpoint else "?")+params),headers={"Authorization":f"Bearer {os.environ.get('UCOS_AFFILIATE_API_TOKEN','')}","Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=20) as resp: payload=json.loads(resp.read().decode())
        except (urllib.error.URLError,urllib.error.HTTPError,ValueError): return []
        items=payload.get("items",payload) if isinstance(payload,dict) else payload
        if not isinstance(items,list): return []
        result=[]
        for item in items:
            if not isinstance(item,dict): continue
            result.append(ProductCandidate(product_id=str(item.get("product_id",item.get("id",""))),title=str(item.get("title","")),url=str(item.get("url","")),relevance=float(item.get("relevance",0) or 0),intent_match=float(item.get("intent_match",0) or 0),verified=bool(item.get("verified",False)),metadata=item.get("metadata") or {}))
        return result
    def select(self, topic: str, niche: str, platform: str):
        return ProductAffiliateSelector().select(self.search(topic,niche,platform),require_verified=True)
