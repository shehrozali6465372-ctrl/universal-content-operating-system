"""Central UCOS control plane: account decision -> production pipeline."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.decision_engine import Decision, DecisionEngine
from layers.layer07_publishing.modules.account_control.policy_registry import PolicyRegistry
from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import ContentRequest, PipelineWiring
from layers.layer14_enterprise_integration.modules.master_orchestrator.production_pipeline import ProductionPipeline

class ControlPlane:
    def __init__(self, registry: Optional[AccountRegistry]=None, policies: Optional[PolicyRegistry]=None, pipeline: Optional[PipelineWiring]=None)->None:
        self.registry=registry or AccountRegistry(); self.policies=policies or PolicyRegistry(); self.decisions=DecisionEngine(self.registry,self.policies)
        self.pipeline=pipeline or ProductionPipeline()
    def execute(self,topic:str,platform:Optional[str]=None,account_id:Optional[str]=None,tone:str="professional",style:str="educational",include_image:bool=True)->Dict[str,Any]:
        accounts=self.registry.list(platform=platform,enabled_only=True)
        if account_id:
            account=self.registry.get(account_id)
            if account is None or not account.enabled: raise LookupError(f"unknown or disabled account_id: {account_id}")
            if platform and account.platform!=platform.strip().lower(): raise ValueError(f"account {account_id} belongs to {account.platform}, not {platform}")
            policy=self.policies.get(account.platform)
            decision=Decision(account_id=account.account_id,platform=account.platform,niche=account.niche,topic=topic.strip(),content_type=self.decisions.choose_content_type(account,topic),policy_version=policy.version if policy else None,reasons=["explicit account_id"])
        elif accounts: decision=self.decisions.decide(topic,platform=platform)
        else:
            request=ContentRequest(topic=topic,platform=platform or "facebook",tone=tone,style=style,include_image=include_image)
            return self.pipeline.execute(request).to_dict()
        request=ContentRequest(topic=decision.topic,platform=decision.platform,tone=tone,style=style,include_image=include_image)
        request.metadata.update({"account_id":decision.account_id,"niche":decision.niche,"content_type":decision.content_type,"policy_version":decision.policy_version,"control_plane":"account_decision_engine"})
        result=self.pipeline.execute(request).to_dict(); published=bool(result.get("publish_result") and result["publish_result"].get("success"))
        try:
            from layers.layer09_learning.modules.learning_engine.account_learning import AccountLearningStore
            AccountLearningStore().record(account_id=decision.account_id,platform=decision.platform,niche=decision.niche,topic=decision.topic,quality_score=float(result.get("quality_score") or 0.0),published=published,analytics=result.get("analytics"),content_type=decision.content_type,policy_version=decision.policy_version)
        except Exception as exc: result["account_learning_error"]=str(exc)
        result["decision"]={"account_id":decision.account_id,"platform":decision.platform,"niche":decision.niche,"policy_version":decision.policy_version,"reasons":decision.reasons}
        return result
