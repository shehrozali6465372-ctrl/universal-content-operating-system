"""Central UCOS control plane: account decision -> production pipeline."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
from layers.layer07_publishing.modules.account_control.decision_engine import Decision, DecisionEngine
from layers.layer07_publishing.modules.account_control.policy_registry import PolicyRegistry
from layers.layer07_publishing.modules.account_control.policy_bootstrap import ensure_default_snapshots
from layers.layer10_monetization.modules.affiliate_evidence_provider import AffiliateEvidenceProvider
from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import ContentRequest, PipelineWiring
from layers.layer14_enterprise_integration.modules.master_orchestrator.production_pipeline import ProductionPipeline

class ControlPlane:
    def __init__(self, registry: Optional[AccountRegistry]=None, policies: Optional[PolicyRegistry]=None, pipeline: Optional[PipelineWiring]=None)->None:
        self.registry=registry or AccountRegistry(); self.policies=ensure_default_snapshots(policies or PolicyRegistry()); self.decisions=DecisionEngine(self.registry,self.policies); self.pipeline=pipeline or ProductionPipeline()

    def _account_learning_store(self):
        from layers.layer09_learning.modules.learning_engine.account_learning import AccountLearningStore
        return AccountLearningStore(AccountDataStore(self.registry))

    def sync_meta_accounts(self, default_niche: str = "general") -> Dict[str, Any]:
        """Discover and provision Meta assets using the single System User token."""
        from layers.layer07_publishing.modules.account_control.meta_asset_discovery import MetaAssetDiscovery
        return MetaAssetDiscovery().provision(self.registry, default_niche=default_niche)

    def _learning_scores(self, accounts: list[Any]) -> Dict[str,float]:
        """Return only observed, account-local performance; never synthesize metrics."""
        try:
            store=self._account_learning_store()
            scores: Dict[str,float]={}
            for account in accounts:
                summary=store.performance_summary(account.account_id)
                if summary.get("observations",0)>0 and summary.get("quality_average") is not None:
                    quality=max(0.0,min(1.0,float(summary["quality_average"])))
                    published=float(summary.get("published_rate") or 0.0)
                    scores[account.account_id]=0.7*quality+0.3*max(0.0,min(1.0,published))
            return scores
        except Exception:
            return {}

    def execute(self,topic:str,platform:Optional[str]=None,account_id:Optional[str]=None,tone:str="professional",style:str="educational",include_image:bool=True)->Dict[str,Any]:
        accounts=self.registry.list(platform=platform,enabled_only=True)
        account=None
        if account_id:
            account=self.registry.get(account_id)
            if account is None or not account.enabled: raise LookupError(f"unknown or disabled account_id: {account_id}")
            if platform and account.platform!=platform.strip().lower(): raise ValueError(f"account {account_id} belongs to {account.platform}, not {platform}")
            policy=self.policies.get(account.platform); product=AffiliateEvidenceProvider().select(topic,account.niche,account.platform)
            decision=Decision(account_id=account.account_id,platform=account.platform,niche=account.niche,topic=topic.strip(),content_type=self.decisions.choose_content_type(account,topic),product=product,affiliate=product,policy_version=policy.version if policy else None,reasons=["explicit account_id","account-scoped affiliate evidence"])
        elif accounts:
            learning_scores=self._learning_scores(accounts)
            decision=self.decisions.decide(topic,platform=platform,learning_scores=learning_scores); account=self.registry.get(decision.account_id); product=AffiliateEvidenceProvider().select(decision.topic,decision.niche,decision.platform)
            decision=Decision(account_id=decision.account_id,platform=decision.platform,niche=decision.niche,topic=decision.topic,content_type=decision.content_type,product=product,affiliate=product,policy_version=decision.policy_version,reasons=decision.reasons+["account-scoped affiliate evidence"])
        else:
            request=ContentRequest(topic=topic,platform=platform or "facebook",tone=tone,style=style,include_image=include_image); return self.pipeline.execute(request).to_dict()
        request=ContentRequest(topic=decision.topic,platform=decision.platform,tone=tone,style=style,include_image=include_image)
        if decision.product: request.style=style+f"; verified affiliate candidate: {decision.product['title']} | {decision.product['url']}. Mention/link it only when relevant and permitted by platform/account policy."
        request.metadata.update({"account_id":decision.account_id,"niche":decision.niche,"credentials_ref":account.credentials_ref if account else "","affiliate_rules":account.affiliate_rules if account else {},"content_type":decision.content_type,"policy_version":decision.policy_version,"product":decision.product,"affiliate":decision.affiliate,"control_plane":"account_decision_engine"})
        result=self.pipeline.execute(request).to_dict(); published=bool(result.get("publish_result") and result["publish_result"].get("success"))
        try:
            local=AccountDataStore(self.registry)
            learning=self._account_learning_store()
            learning.record(account_id=decision.account_id,platform=decision.platform,niche=decision.niche,topic=decision.topic,quality_score=float(result.get("quality_score") or 0.0),published=published,analytics=result.get("analytics"),content_type=decision.content_type,policy_version=decision.policy_version)
            publish_meta=(result.get("publish_result") or {}).get("metadata") or {}
            local.append(decision.account_id,"content","execution_history",{
                "timestamp":__import__("time").time(),"topic":decision.topic,"platform":decision.platform,"niche":decision.niche,
                "content_type":decision.content_type,"quality_score":float(result.get("quality_score") or 0.0),"published":published,
                "post_id":(result.get("publish_result") or {}).get("post_id"),"title":result.get("title"),"text":result.get("text"),
                "policy_version":decision.policy_version,"product":decision.product,"affiliate":decision.affiliate,
                "template_id":publish_meta.get("template_id"),"template_fingerprint":publish_meta.get("template_fingerprint"),
            })
            local.append(decision.account_id,"analytics","execution_outcomes",{
                "timestamp":__import__("time").time(),"topic":decision.topic,"platform":decision.platform,
                "quality_score":float(result.get("quality_score") or 0.0),"published":published,
                "post_id":(result.get("publish_result") or {}).get("post_id"),"analytics":result.get("analytics") if result.get("analytics") is not None else "UNKNOWN",
            })
        except Exception as exc: result["account_learning_error"]=str(exc)
        result["decision"]={"account_id":decision.account_id,"platform":decision.platform,"niche":decision.niche,"content_type":decision.content_type,"policy_version":decision.policy_version,"product":decision.product,"reasons":decision.reasons}
        return result
