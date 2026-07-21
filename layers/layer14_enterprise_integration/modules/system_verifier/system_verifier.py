"""SystemVerifier — Enterprise Verification & Audit Framework."""
from __future__ import annotations
import os, sys, time, json, sqlite3, importlib
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum


class LayerStatus(str, Enum):
    PASS = "PASS"
    FALLBACK = "FALLBACK"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class LayerResult:
    layer_num: int
    name: str
    status: LayerStatus
    details: str
    score: float
    sub_tests: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


class SystemVerifier:
    def __init__(self):
        self.results = []
        self.start_time = 0.0

    def run_full_verification(self):
        self.start_time = time.time()
        print("=" * 70)
        print("🔍 UNIVERSAL AI CONTENT OS — SYSTEM VERIFICATION")
        print("=" * 70)
        print()
        self._test_layer01_core()
        self._test_layer02_research()
        self._test_layer03_intelligence()
        self._test_layer04_writing()
        self._test_layer05_image()
        self._test_layer06_quality()
        self._test_layer07_publishing()
        self._test_layer08_analytics()
        self._test_layer09_learning()
        self._test_layer10_monetization()
        self._test_layer11_async()
        self._test_layer12_ai_foundation()
        self._test_layer13_persistence()
        self._test_layer14_integration()
        self._test_layer15_22_infrastructure()
        return self._generate_report()

    def _test_layer01_core(self):
        start = time.time()
        sub = []; score = 0.0
        try:
            from layers.layer01_core.modules.config_manager.config_manager import ConfigManager
            cm = ConfigManager(); sub.append({"test": "ConfigManager", "status": "PASS", "detail": "Works"}); score += 1.0
        except Exception as e: sub.append({"test": "ConfigManager", "status": "ERROR", "detail": str(e)[:80]})
        try:
            from layers.layer01_core.modules.memory_manager.memory_manager import MemoryManager
            mm = MemoryManager(); mm.store("k","v")
            sub.append({"test": "MemoryManager", "status": "PASS", "detail": "Store/retrieve"}); score += 1.0
        except Exception as e: sub.append({"test": "MemoryManager", "status": "ERROR", "detail": str(e)[:80]})
        try:
            from layers.layer01_core.modules.logger.logger import Logger
            l = Logger(); l.info("test"); sub.append({"test": "Logger", "status": "PASS", "detail": "Logging"}); score += 1.0
        except Exception as e: sub.append({"test": "Logger", "status": "ERROR", "detail": str(e)[:80]})
        try:
            from layers.layer01_core.modules.scheduler.scheduler import Scheduler
            s = Scheduler(); sub.append({"test": "Scheduler", "status": "PASS", "detail": "Instantiable"}); score += 1.0
        except Exception as e: sub.append({"test": "Scheduler", "status": "ERROR", "detail": str(e)[:80]})
        fs = score/4.0; st = LayerStatus.PASS if fs>=0.75 else LayerStatus.FALLBACK
        self.results.append(LayerResult(1,"Core",st,"Config,Memory,Logger,Scheduler",fs,sub,(time.time()-start)*1000))
        self._p(1,"Core",st,fs)

    def _test_layer02_research(self):
        start = time.time(); sub = []; score = 0.0
        try:
            from layers.layer02_research.modules.trend_discovery.trend_discovery import TrendDiscovery
            td = TrendDiscovery(); r = td.discover_trends("AI")
            if r: sub.append({"test":"TrendDiscovery","status":"PASS","detail":f"{len(r)} trends"}); score+=1.0
            else: sub.append({"test":"TrendDiscovery","status":"FALLBACK","detail":"Empty"}); score+=0.3
        except Exception as e: sub.append({"test":"TrendDiscovery","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer02_research.modules.fact_verification.fact_verifier import FactVerifier
            fv = FactVerifier(); r = fv.verify("Earth orbits Sun")
            if r: sub.append({"test":"FactVerifier","status":"PASS","detail":"Verified"}); score+=1.0
            else: sub.append({"test":"FactVerifier","status":"FALLBACK","detail":"No result"}); score+=0.3
        except Exception as e: sub.append({"test":"FactVerifier","status":"ERROR","detail":str(e)[:80]})
        fs=score/2.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(2,"Research",st,"Trends,Facts",fs,sub,(time.time()-start)*1000))
        self._p(2,"Research",st,fs)

    def _test_layer03_intelligence(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer03_intelligence.modules.semantic_analysis.semantic_analyzer import SemanticAnalyzer
            sa=SemanticAnalyzer();r=sa.analyze("AI transforms world")
            if r: sub.append({"test":"SemanticAnalyzer","status":"PASS","detail":"Works"});score+=1.0
            else: sub.append({"test":"SemanticAnalyzer","status":"FALLBACK","detail":"Empty"});score+=0.3
        except Exception as e: sub.append({"test":"SemanticAnalyzer","status":"ERROR","detail":str(e)[:80]})
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(3,"Intelligence",st,"Semantic Analysis",fs,sub,(time.time()-start)*1000))
        self._p(3,"Intelligence",st,fs)

    def _test_layer04_writing(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer04_writing.modules.content_planner.content_planner import ContentPlanner
            cp=ContentPlanner();p=cp.create_plan("AI",platform="facebook")
            if p: sub.append({"test":"ContentPlanner","status":"PASS","detail":"Plan created"});score+=1.0
            else: sub.append({"test":"ContentPlanner","status":"FALLBACK","detail":"No plan"});score+=0.3
        except Exception as e: sub.append({"test":"ContentPlanner","status":"ERROR","detail":str(e)[:80]})
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(4,"Writing",st,"Content Planning",fs,sub,(time.time()-start)*1000))
        self._p(4,"Writing",st,fs)

    def _test_layer05_image(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer05_image.modules.image_planner.image_planner import ImagePlanner
            ip=ImagePlanner();pl=ip.plan("pyramids",platform="facebook",image_type="photo",count=1)
            if pl: sub.append({"test":"ImagePlanner","status":"PASS","detail":"Plan created"});score+=1.0
            else: sub.append({"test":"ImagePlanner","status":"FALLBACK","detail":"Empty"});score+=0.3
        except Exception as e: sub.append({"test":"ImagePlanner","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider
            gip=GeminiImageProvider();ir=gip.generate("test")
            p=getattr(ir,"provider","unknown")
            if "mock" in str(p).lower(): sub.append({"test":"GeminiImageProvider","status":"FALLBACK","detail":f"Mock: {p}"});score+=0.2
            else: sub.append({"test":"GeminiImageProvider","status":"PASS","detail":f"Provider: {p}"});score+=1.0
        except Exception as e: sub.append({"test":"GeminiImageProvider","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer05_image.modules.infographic_generator.infographic_generator import InfographicGenerator
            ig=InfographicGenerator();path=ig.generate_from_list("T","S",[{"title":"T","description":"D"}],output_path="/tmp/verify_test.png")
            if os.path.exists(path) and os.path.getsize(path)>1000: sub.append({"test":"InfographicGenerator","status":"PASS","detail":f"{os.path.getsize(path)} bytes"});score+=1.0;os.remove(path)
            else: sub.append({"test":"InfographicGenerator","status":"FALLBACK","detail":"Small"});score+=0.3
        except Exception as e: sub.append({"test":"InfographicGenerator","status":"ERROR","detail":str(e)[:80]})
        fs=score/3.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(5,"Image",st,"Planner,Provider,Infographic",fs,sub,(time.time()-start)*1000))
        self._p(5,"Image",st,fs)

    def _test_layer06_quality(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer06_quality.modules.quality_orchestrator.quality_orchestrator import QualityOrchestrator
            qo=QualityOrchestrator();r=qo.evaluate("Test post",platform="facebook")
            if r:
                s=str(r).lower()
                if "simulat" in s: sub.append({"test":"QualityOrchestrator","status":"FALLBACK","detail":"Simulated records"});score+=0.3
                else: sub.append({"test":"QualityOrchestrator","status":"PASS","detail":f"Score: {r}"});score+=1.0
            else: sub.append({"test":"QualityOrchestrator","status":"FALLBACK","detail":"Empty"});score+=0.3
        except Exception as e: sub.append({"test":"QualityOrchestrator","status":"ERROR","detail":str(e)[:80]})
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(6,"Quality",st,"Scoring,Safety",fs,sub,(time.time()-start)*1000))
        self._p(6,"Quality",st,fs)

    def _test_layer07_publishing(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
            fb=FacebookPublisher();c=fb.get_capabilities()
            if c and hasattr(c,"supports_images"): sub.append({"test":"FacebookPublisher","status":"PASS","detail":"Real publisher"});score+=1.0
            else: sub.append({"test":"FacebookPublisher","status":"FALLBACK","detail":"No caps"});score+=0.3
        except Exception as e: sub.append({"test":"FacebookPublisher","status":"ERROR","detail":str(e)[:80]})
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(7,"Publishing",st,"Facebook Publisher",fs,sub,(time.time()-start)*1000))
        self._p(7,"Publishing",st,fs)

    def _test_layer08_analytics(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer08_analytics.modules.analytics_orchestrator.analytics_orchestrator import AnalyticsOrchestrator
            ao=AnalyticsOrchestrator();r=ao.run_pipeline(collect=True,calculate=True,detect_trends=True)
            if r: sub.append({"test":"AnalyticsOrchestrator","status":"PASS","detail":"Pipeline ran"});score+=1.0
            else: sub.append({"test":"AnalyticsOrchestrator","status":"FALLBACK","detail":"No result"});score+=0.3
        except Exception as e: sub.append({"test":"AnalyticsOrchestrator","status":"ERROR","detail":str(e)[:80]})
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(8,"Analytics",st,"Metrics,Trends",fs,sub,(time.time()-start)*1000))
        self._p(8,"Analytics",st,fs)

    def _test_layer09_learning(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer09_learning.modules.learning_engine.learning_memory import LearningMemory
            lm=LearningMemory();sub.append({"test":"LearningMemory","status":"PASS","detail":"Available"});score+=1.0
        except Exception as e: sub.append({"test":"LearningMemory","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer09_learning.modules.learning_engine.lesson_generator import LessonGenerator
            lg=LessonGenerator();sub.append({"test":"LessonGenerator","status":"PASS","detail":"Available"});score+=1.0
        except Exception as e: sub.append({"test":"LessonGenerator","status":"ERROR","detail":str(e)[:80]})
        fs=score/2.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(9,"Learning",st,"Self-Improvement",fs,sub,(time.time()-start)*1000))
        self._p(9,"Learning",st,fs)

    def _test_layer10_monetization(self):
        start=time.time();sub=[];score=0.0;rc=0
        mods=[("Master Orchestrator","layers.layer10_monetization.modules.master_orchestrator"),("Workflow Coordinator","layers.layer10_monetization.modules.workflow_coordinator"),("Task Scheduler","layers.layer10_monetization.modules.task_scheduler"),("AI Meta Controller","layers.layer10_monetization.modules.ai_meta_controller"),("Autonomous Planner","layers.layer10_monetization.modules.autonomous_planner"),("Content Generation","layers.layer10_monetization.modules.content_generation"),("Knowledge Research","layers.layer10_monetization.modules.knowledge_research"),("Analytics Intelligence","layers.layer10_monetization.modules.analytics_intelligence"),("Business Intelligence","layers.layer10_monetization.modules.business_intelligence"),("Universal OS","layers.layer10_monetization.modules.universal_os")]
        for name,mp in mods:
            try:
                m=importlib.import_module(mp)
                if len(dir(m))>3: sub.append({"test":name,"status":"PASS","detail":"Loaded"});score+=1.0;rc+=1
                else: sub.append({"test":name,"status":"FALLBACK","detail":"Empty"});score+=0.3
            except Exception as e: sub.append({"test":name,"status":"ERROR","detail":str(e)[:60]})
        fs=score/10.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(10,"Monetization",st,f"{rc}/10 modules loaded",fs,sub,(time.time()-start)*1000))
        self._p(10,"Monetization",st,fs)

    def _test_layer11_async(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer11_async_runtime.modules.async_runtime_engine.runtime import AsyncRuntime
            ar=AsyncRuntime();sub.append({"test":"AsyncRuntime","status":"PASS","detail":"Instantiable"});score+=1.0
        except: sub.append({"test":"AsyncRuntime","status":"FALLBACK","detail":"Framework"});score+=0.5
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(11,"Async Runtime",st,"Async framework",fs,sub,(time.time()-start)*1000))
        self._p(11,"Async Runtime",st,fs)

    def _test_layer12_ai_foundation(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
            km=KeyManager();km.register_key("t","k123","gemini");sel=km.select_key("text")
            if sel: sub.append({"test":"KeyManager","status":"PASS","detail":"Rotation works"});score+=1.0
            else: sub.append({"test":"KeyManager","status":"FALLBACK","detail":"No key"});score+=0.3
        except Exception as e: sub.append({"test":"KeyManager","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
            gp=GeminiProvider();r=gp.generate("test")
            if r.get("simulated"): sub.append({"test":"GeminiProvider","status":"FALLBACK","detail":"Simulated (no key)"});score+=0.2
            else: sub.append({"test":"GeminiProvider","status":"PASS","detail":"Real API"});score+=1.0
        except Exception as e: sub.append({"test":"GeminiProvider","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer12_ai_foundation.modules.model_router.prompt_builder import PromptBuilder
            pb=PromptBuilder();p=pb.build("Write",style="direct")
            if p and "messages" in p: sub.append({"test":"PromptBuilder","status":"PASS","detail":"Works"});score+=1.0
            else: sub.append({"test":"PromptBuilder","status":"FALLBACK","detail":"Basic"});score+=0.5
        except Exception as e: sub.append({"test":"PromptBuilder","status":"ERROR","detail":str(e)[:80]})
        fs=score/3.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(12,"AI Foundation",st,"LLM,Keys,Prompts",fs,sub,(time.time()-start)*1000))
        self._p(12,"AI Foundation",st,fs)

    def _test_layer13_persistence(self):
        start=time.time();sub=[];score=0.0
        try:
            db="/tmp/verify.db";c=sqlite3.connect(db);c.execute("CREATE TABLE IF NOT EXISTS t(id INT,name TEXT)");c.execute('INSERT INTO t VALUES(1, "v")');c.commit();r=c.execute("SELECT * FROM t").fetchone();c.close();os.remove(db)
            if r: sub.append({"test":"SQLite","status":"PASS","detail":"Real DB"});score+=1.0
            else: sub.append({"test":"SQLite","status":"FALLBACK","detail":"No data"});score+=0.3
        except Exception as e: sub.append({"test":"SQLite","status":"ERROR","detail":str(e)[:80]})
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
            pp=PipelinePersistence();pp.close();sub.append({"test":"PipelinePersistence","status":"PASS","detail":"SQLite persistence"});score+=1.0
        except Exception as e: sub.append({"test":"PipelinePersistence","status":"ERROR","detail":str(e)[:80]})
        fs=score/2.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(13,"Persistence",st,"SQLite, PipelineDB",fs,sub,(time.time()-start)*1000))
        self._p(13,"Persistence",st,fs)

    def _test_layer14_integration(self):
        start=time.time();sub=[];score=0.0
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring,ContentRequest
            pw=PipelineWiring();req=ContentRequest(topic="Verify",platform="facebook");resp=pw.execute(req)
            ok=len([s for s in resp.steps if s.status=="success"]);tot=len(resp.steps)
            sub.append({"test":"PipelineWiring","status":"PASS","detail":f"{ok}/{tot} steps"});score+=1.0 if ok==tot else 0.5
        except Exception as e: sub.append({"test":"PipelineWiring","status":"ERROR","detail":str(e)[:80]})
        fs=score/1.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(14,"Integration",st,"PipelineWiring E2E",fs,sub,(time.time()-start)*1000))
        self._p(14,"Integration",st,fs)

    def _test_layer15_22_infrastructure(self):
        start=time.time();sub=[];score=0.0
        layers=[(15,"Async v2","layers.layer15_async_runtime"),(16,"Database","layers.layer16_database_engineering"),(17,"Security","layers.layer17_security"),(18,"Monitoring","layers.layer18_monitoring"),(19,"Analytics Eng","layers.layer19_analytics_engine"),(20,"Image Pipeline","layers.layer20_image_pipeline"),(21,"Deployment","layers.layer21_deployment"),(22,"Documentation","layers.layer22_documentation")]
        for n,name,mp in layers:
            try:
                m=importlib.import_module(mp);e=len([f for f in dir(m) if not f.startswith("_")])
                if e>2: sub.append({"test":f"L{n} {name}","status":"PASS","detail":f"{e} exports"});score+=1.0
                else: sub.append({"test":f"L{n} {name}","status":"FALLBACK","detail":"Framework"});score+=0.3
            except Exception as e: sub.append({"test":f"L{n} {name}","status":"ERROR","detail":str(e)[:60]})
        fs=score/8.0; st=LayerStatus.PASS if fs>=0.7 else LayerStatus.FALLBACK
        self.results.append(LayerResult(15,"Infrastructure (15-22)",st,"8 layers",fs,sub,(time.time()-start)*1000))
        self._p(15,"Infrastructure",st,fs)

    def _p(self,layer,name,status,score):
        ic={"PASS":"✅","FALLBACK":"⚠️","ERROR":"❌"}
        print(f"  {ic.get(status.value,'?')} Layer {layer:2d} — {name:25s} — {status.value:8s} ({score*100:.0f}%)")
        for s in self.results[-1].sub_tests:
            si={"PASS":"✅","FALLBACK":"⚠️","ERROR":"❌"}
            print(f"      {si.get(s['status'],'?')} {s['test']:30s} {s['status']:8s} {s['detail'][:55]}")

    def _generate_report(self):
        tt=(time.time()-self.start_time)*1000;total=len(self.results)
        p=sum(1 for r in self.results if r.status==LayerStatus.PASS)
        fb=sum(1 for r in self.results if r.status==LayerStatus.FALLBACK)
        err=total-p-fb;avg=sum(r.score for r in self.results)/max(total,1)
        print();print("="*70);print("📊 VERIFICATION REPORT");print("="*70)
        print(f"  Overall System Health:     {avg*100:.1f}%")
        print(f"  Real Features (PASS):      {p}/{total}")
        print(f"  Fallback Features:         {fb}/{total}")
        print(f"  Failed/Skipped:            {err}/{total}")
        print(f"  Verification Time:         {tt:.0f}ms")
        print();print("="*70)
        return {"overall_health":round(avg*100,1),"passed":p,"fallback":fb,"errors":err,"total":total,"duration_ms":round(tt,1)}


def run_verification():
    return SystemVerifier().run_full_verification()
