"""Central UCOS control plane: account decision -> production pipeline."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.decision_engine import Decision, DecisionEngine
from layers.layer07_publishing.modules.account_control.policy_registry import PolicyRegistry
from layers.layer07_publishing.modules.account_control.policy_bootstrap import ensure_default_snapshots
from layers.layer10_monetization.modules.affiliate_evidence_provider import AffiliateEvidenceProvider
from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import ContentRequest, PipelineWiring
from layers.layer14_enterprise_integration.modules.master_orchestrator.production_pipeline import ProductionPipeline

class ControlPlane:
    def __init__(self, registry: Optional[AccountRegistry]=None, policies: Optional[PolicyRegistry]=None, pipeline: Optional[PipelineWiring]=None)->None:
        self.registry=registry or AccountRegistry(); self.policies=ensure_default_snapshots(policies or PolicyRegistry()); self.decisions=DecisionEngine(self.registry,self.policies); self.pipeline=pipeline or ProductionPipeline()
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
            decision=self.decisions.decide(topic,platform=platform); account=self.registry.get(decision.account_id); product=AffiliateEvidenceProvider().select(decision.topic,decision.niche,decision.platform)
            decision=Decision(account_id=decision.account_id,platform=decision.platform,niche=decision.niche,topic=decision.topic,content_type=decision.content_type,product=product,affiliate=product,policy_version=decision.policy_version,reasons=decision.reasons+["account-scoped affiliate evidence"])
        else:
            request=ContentRequest(topic=topic,platform=platform or "facebook",tone=tone,style=style,include_image=include_image); return self.pipeline.execute(request).to_dict()
        request=ContentRequest(topic=decision.topic,platform=decision.platform,tone=tone,style=style,include_image=include_image)
        if decision.product: request.style=style+f"; verified affiliate candidate: {decision.product['title']} | {decision.product['url']}. Mention/link it only when relevant and permitted by platform/account policy."
        request.metadata.update({"account_id":decision.account_id,"niche":decision.niche,"credentials_ref":account.credentials_ref if account else "","affiliate_rules":account.affiliate_rules if account else {},"content_type":decision.content_type,"policy_version":decision.policy_version,"product":decision.product,"affiliate":decision.affiliate,"control_plane":"account_decision_engine"})
        result=self.pipeline.execute(request).to_dict(); published=bool(result.get("publish_result") and result["publish_result"].get("success"))
        try:
            from layers.layer09_learning.modules.learning_engine.account_learning import AccountLearningStore
            AccountLearningStore().record(account_id=decision.account_id,platform=decision.platform,niche=decision.niche,topic=decision.topic,quality_score=float(result.get("quality_score") or 0.0),published=published,analytics=result.get("analytics"),content_type=decision.content_type,policy_version=decision.policy_version)
        except Exception as exc: result["account_learning_error"]=str(exc)
        result["decision"]={"account_id":decision.account_id,"platform":decision.platform,"niche":decision.niche,"content_type":decision.content_type,"policy_version":decision.policy_version,"product":decision.product,"reasons":decision.reasons}
        return result
