"""
Universal AI Content Operating System
Main Entry Point

Usage:
    python main.py                    # Boot full system
    python main.py --generate "topic" # Generate content
    python main.py --status           # Show system status
"""
from __future__ import annotations
import os
import sys
import time
import json
from typing import Any, Dict, Optional


# GitHub Secret names (note: key 2 & 3 have no underscores)
GEMINI_KEY_NAMES = [
    ("GEMINI_API_KEY_1", "GEMINI_API_KEY_1"),
    ("GEMINI_API_KEY_2", "GEMINIAPIKEY2"),
    ("GEMINI_API_KEY_3", "GEMINIAPIKEY3"),
]


def load_env_secrets() -> Dict[str, str]:
    """Load API keys from environment / GitHub Secrets."""
    secrets = {}
    for env_name, secret_name in GEMINI_KEY_NAMES:
        key = os.environ.get(env_name) or os.environ.get(secret_name)
        if key:
            secrets[secret_name] = key
    return secrets


LAYER_MAP = [
    ("Layer 1 — Core", "layers.layer01_core"),
    ("Layer 14 — Integration", "layers.layer14_enterprise_integration"),
    ("Layer 17 — Security", "layers.layer17_security"),
    ("Layer 18 — Monitoring", "layers.layer18_monitoring"),
    ("Layer 12 — AI Foundation", "layers.layer12_ai_foundation"),
    ("Layer 16 — Database", "layers.layer16_database_engineering"),
    ("Layer 15 — Async Runtime", "layers.layer15_async_runtime"),
    ("Layer 2 — Research", "layers.layer02_research"),
    ("Layer 3 — Intelligence", "layers.layer03_intelligence"),
    ("Layer 4 — Writing", "layers.layer04_writing"),
    ("Layer 5 — Image", "layers.layer05_image"),
    ("Layer 6 — Quality", "layers.layer06_quality"),
    ("Layer 7 — Publishing", "layers.layer07_publishing"),
    ("Layer 8 — Analytics", "layers.layer08_analytics"),
    ("Layer 9 — Learning", "layers.layer09_learning"),
    ("Layer 10 — Monetization", "layers.layer10_monetization"),
    ("Layer 19 — Analytics Engine", "layers.layer19_analytics_engine"),
    ("Layer 20 — Image Pipeline", "layers.layer20_image_pipeline"),
    ("Layer 21 — Deployment", "layers.layer21_deployment"),
    ("Layer 22 — Documentation", "layers.layer22_documentation"),
    ("Layer 23 — Website Manager", "layers.layer23_website_manager"),
]


class AIOSBoot:
    """Universal AI Content Operating System — Boot Sequence."""

    def __init__(self) -> None:
        self.start_time = time.time()
        self.version = "6.0.0"
        self.layers_loaded: list = []
        self.errors: list = []

    def boot(self) -> Dict[str, Any]:
        print(f"🤖 Universal AI Content Operating System v{self.version}")
        print("=" * 60)

        for name, module_path in LAYER_MAP:
            try:
                __import__(module_path)
                self.layers_loaded.append(name)
                print(f"  ✅ {name}")
            except Exception as exc:
                self.errors.append({"layer": name, "error": str(exc)})
                print(f"  ⚠️  {name} — {exc}")

        elapsed = round(time.time() - self.start_time, 2)
        total = len(LAYER_MAP)
        loaded = len(self.layers_loaded)
        print(f"\n{'=' * 60}")
        print(f"✅ Boot complete: {loaded}/{total} layers in {elapsed}s")
        if self.errors:
            print(f"⚠️  {len(self.errors)} errors during boot")

        return {
            "version": self.version,
            "layers_loaded": loaded,
            "layers": self.layers_loaded,
            "errors": self.errors,
            "boot_time_seconds": elapsed,
        }


def generate_content(topic: str, platform: str = "facebook",
                    tone: str = "professional", style: str = "educational",
                    include_image: bool = True) -> Dict[str, Any]:
    """Run the full end-to-end pipeline for a topic."""
    try:
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
            PipelineWiring, ContentRequest,
        )

        pipe = PipelineWiring()
        req = ContentRequest(
            topic=topic, platform=platform, tone=tone,
            style=style, include_image=include_image,
        )
        response = pipe.execute(req)
        return response.to_dict()
    except Exception as exc:
        return {"topic": topic, "error": str(exc), "traceback": __import__("traceback").format_exc()}


def show_status() -> Dict[str, Any]:
    """Show current system status."""
    import glob
    layer_dirs = sorted(glob.glob("layers/layer*/"))
    total_files = sum(
        len(glob.glob(f"{d}**/*.py", recursive=True))
        for d in layer_dirs
    )
    return {
        "version": "6.0.0",
        "total_layers": len(layer_dirs),
        "total_python_files": total_files,
        "layers": [os.path.basename(d.rstrip("/")) for d in layer_dirs],
    }



def show_analytics() -> Dict[str, Any]:
    """Show analytics summary from database."""
    try:
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        persist = PipelinePersistence()
        summary = persist.get_analytics_summary()
        persist.close()
        return {"analytics": summary, "total_metrics": len(summary)}
    except Exception as exc:
        return {"error": str(exc)}


def show_history(limit: int = 10, platform: Optional[str] = None) -> Dict[str, Any]:
    """Show content history from database."""
    try:
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        persist = PipelinePersistence()
        history = persist.get_content_history(platform=platform, limit=limit)
        persist.close()
        return {"history": history, "count": len(history), "platform_filter": platform}
    except Exception as exc:
        return {"error": str(exc)}


def show_stats() -> Dict[str, Any]:
    """Show full system statistics."""
    import glob
    layer_dirs = sorted(glob.glob("layers/layer*/"))
    total_files = sum(
        len(glob.glob(f"{d}**/*.py", recursive=True))
        for d in layer_dirs
    )
    test_files = len(glob.glob("tests/**/test_*.py", recursive=True))

    db_stats = {}
    try:
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        persist = PipelinePersistence()
        db_stats = persist.get_db_stats()
        persist.close()
    except Exception:
        pass

    return {
        "version": "6.0.0",
        "layers": len(layer_dirs),
        "source_files": total_files,
        "test_files": test_files,
        "database": db_stats,
    }



if __name__ == "__main__":
    args = sys.argv[1:]

    if "--status" in args:
        status = show_status()
        print(json.dumps(status, indent=2))

    elif "--topic" in args:
        # Full end-to-end pipeline
        idx = args.index("--topic")
        topic = args[idx + 1] if idx + 1 < len(args) else "artificial intelligence"
        platform = "facebook"
        tone = "professional"
        if "--platform" in args:
            pidx = args.index("--platform")
            platform = args[pidx + 1] if pidx + 1 < len(args) else "facebook"
        if "--tone" in args:
            tidx = args.index("--tone")
            tone = args[tidx + 1] if tidx + 1 < len(args) else "professional"
        result = generate_content(topic, platform=platform, tone=tone)
        print(json.dumps(result, indent=2, default=str))

    elif "--generate" in args:
        # Legacy: single-topic Gemini generation
        idx = args.index("--generate")
        topic = args[idx + 1] if idx + 1 < len(args) else "artificial intelligence"
        result = generate_content(topic)
        print(json.dumps(result, indent=2, default=str))

    elif "--analytics" in args:
        result = show_analytics()
        print(json.dumps(result, indent=2, default=str))

    elif "--history" in args:
        limit = 10
        platform = None
        if "--limit" in args:
            lidx = args.index("--limit")
            limit = int(args[lidx + 1]) if lidx + 1 < len(args) else 10
        if "--platform" in args:
            pidx = args.index("--platform")
            platform = args[pidx + 1] if pidx + 1 < len(args) else None
        result = show_history(limit=limit, platform=platform)
        print(json.dumps(result, indent=2, default=str))

    elif "--stats" in args:
        result = show_stats()
        print(json.dumps(result, indent=2, default=str))

    elif "--api" in args:
        from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway
        port = 8000
        if "--port" in args:
            pidx = args.index("--port")
            port = int(args[pidx + 1]) if pidx + 1 < len(args) else 8000
        gateway = APIGateway(port=port)
        gateway.start()
        print(f"\n🌐 API Gateway running on http://0.0.0.0:{port}")
        print(f"   Endpoints: /status /health /analytics /history /stats /generate /templates /platforms")
        print(f"   Press Ctrl+C to stop\n")
        try:
            import signal
            signal.signal(signal.SIGINT, lambda s, f: (gateway.stop(), print("\n🛑 Gateway stopped"), sys.exit(0)))
            signal.pause()
        except AttributeError:
            import time as _time
            while gateway.is_running():
                _time.sleep(1)

    elif "--schedule" in args:
        from layers.layer07_publishing.modules.content_scheduler.scheduler import ContentScheduler
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        scheduler = ContentScheduler()
        idx = args.index("--schedule")
        cron = args[idx + 1] if idx + 1 < len(args) else "daily"
        topic_idx = args.index("--topic") if "--topic" in args else -1
        topic = args[topic_idx + 1] if topic_idx >= 0 and topic_idx + 1 < len(args) else "AI Trends"
        platforms = ["facebook"]
        if "--platforms" in args:
            pidx = args.index("--platforms")
            platforms = args[pidx + 1].split(",") if pidx + 1 < len(args) else ["facebook"]
        job = scheduler.add_job(topic=topic, platforms=platforms, cron=cron)
        print(json.dumps({"job": job.to_dict(), "message": f"Scheduled '{topic}' on {cron} for {platforms}"}, indent=2, default=str))

    elif "--scheduler-stats" in args:
        from layers.layer07_publishing.modules.content_scheduler.scheduler import ContentScheduler
        scheduler = ContentScheduler()
        print(json.dumps(scheduler.get_stats(), indent=2))

    elif "--cron-next" in args:
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        idx = args.index("--cron-next")
        expr = CronExpression(args[idx + 1] if idx + 1 < len(args) else "daily")
        nxt = expr.next_run_time()
        print(json.dumps({"expression": str(expr), "next_run": nxt.isoformat() if nxt else "none"}, indent=2))

    elif "--cron-presets" in args:
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression()
        presets = {name: cron.get_preset(name) for name in cron.list_presets()}
        print(json.dumps(presets, indent=2))

    elif "--cross-publish" in args:
        from layers.layer07_publishing.modules.platform_plugin_manager.cross_platform_publisher import CrossPlatformPublisher
        cross = CrossPlatformPublisher()
        idx = args.index("--cross-publish")
        topic = args[idx + 1] if idx + 1 < len(args) else "AI Trends"
        result = cross.publish(topic=topic, content=f"Check out the latest on {topic}!", platforms=["facebook"])
        print(json.dumps(result.to_dict(), indent=2, default=str))

    elif "--dashboard" in args:
        import http.server
        import os
        dash_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard")
        if not os.path.exists(os.path.join(dash_dir, "dashboard.html")):
            print("⚠️  Dashboard not found. Run from project root.")
            sys.exit(1)
        port = 8080
        if "--port" in args:
            pidx = args.index("--port")
            port = int(args[pidx + 1]) if pidx + 1 < len(args) else 8080
        os.chdir(dash_dir)
        handler = http.server.SimpleHTTPRequestHandler
        with http.server.HTTPServer(("0.0.0.0", port), handler) as httpd:
            print(f"\n🖥️  Dashboard at http://localhost:{port}/dashboard.html")
            print(f"   API Gateway should be on port 8000")
            print(f"   Press Ctrl+C to stop\n")
            httpd.serve_forever()

    elif "--production" in args:
        from layers.layer14_enterprise_integration.modules.production_certification.production_certifier import ProductionCertifier
        certifier = ProductionCertifier()
        report = certifier.run_full_certification()
        print(f"\n📋 Full report saved to memory")
        print(json.dumps(report, indent=2, default=str))

    elif "--live-proof" in args:
        from layers.layer14_enterprise_integration.modules.production_certification.live_proof import LiveProof
        lp = LiveProof()
        report = lp.run()
        print(json.dumps(report, indent=2, default=str))

    elif "--prove-all" in args:
        from layers.layer14_enterprise_integration.modules.production_certification.prove_all import ProveAll
        prover = ProveAll()
        report = prover.run()
        print(json.dumps(report, indent=2, default=str))

    elif "--proof" in args:
        from layers.layer14_enterprise_integration.modules.production_certification.proof_verifier import ProofVerifier
        verifier = ProofVerifier()
        report = verifier.run_full_verification()
        print(json.dumps(report, indent=2, default=str))

    elif "--verify-system" in args:
        from layers.layer14_enterprise_integration.modules.system_verifier.system_verifier import run_verification
        report = run_verification()
        print(f"\n📋 Full report saved to memory")
        print(json.dumps(report, indent=2, default=str))

    elif "--db-status" in args:
        from layers.layer13_persistence.modules.postgresql.manager import get_database
        db = get_database()
        status = db.get_db_status()
        # Pretty print
        print("\n🐘 DATABASE STATUS")
        print("=" * 50)
        print(f"  Overall     : {status['overall']}")
        print(f"  PostgreSQL  : {'✅' if status['postgresql_available'] else '⚠️  SQLite fallback'}")
        print()
        print("  📊 Connections:")
        conn = status['connections']
        print(f"     Active    : {conn['active']}")
        print(f"     Idle      : {conn['idle']}")
        print(f"     Max Pool  : {conn['max_pool_size']}")
        print(f"     Queries   : {conn['total_queries']:,}")
        print(f"     Failed    : {conn['failed_queries']}")
        print(f"     Retries   : {conn['total_retries']}")
        print()
        print("  ⏱️  Latency:")
        lat = status['latency']
        print(f"     Avg       : {lat['avg_ms']}ms")
        print(f"     P95       : {lat['p95_ms']}ms")
        print(f"     P99       : {lat['p99_ms']}ms")
        print()
        slow = status['slow_queries']
        if slow['total'] > 0:
            print(f"  🐌 Slow Queries: {slow['total']} ({slow['slow_pct']}%)")
        leak = status['leak_detection']
        if leak['total_leaks_detected'] > 0:
            print(f"  🔴 Leaks Detected: {leak['total_leaks_detected']}")
        print()
        print(f"  📦 Tables: {len(status['tables'])} | Rows: {status['total_rows']:,}")
        print("=" * 50)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--postgres-transaction-recovery" in args:
        from layers.layer13_persistence.modules.postgresql.manager import get_database
        db = get_database()
        result = db.run_transaction_recovery()
        print(json.dumps(result, indent=2, default=str))

    elif "--postgres-leak-check" in args:
        from layers.layer13_persistence.modules.postgresql.manager import get_database
        db = get_database()
        leaks = db.check_leaks()
        stats = db.leak_detector.get_stats() if db.leak_detector else {}
        print(f"\n🔍 Leak Detection: {len(leaks)} active leaks")
        print(json.dumps(stats, indent=2, default=str))


    elif "--redis-status" in args:
        from layers.layer13_persistence.modules.redis_platform.redis_manager import get_redis
        redis = get_redis()
        status = redis.get_redis_status()
        print("\n🔴 REDIS STATUS")
        print("=" * 50)
        print(f"  Overall     : {status["overall"]}")
        print(f"  Redis       : {"✅ Real Redis" if status["connection"]["redis_available"] else "⚠️  In-memory fallback"}")
        print()
        print("  📊 Connection:")
        conn = status["connection"]
        print(f"     Total Ops : {conn["total_ops"]:,}")
        print(f"     Failed    : {conn["failed_ops"]}")
        print(f"     Retries   : {conn["total_retries"]}")
        print()
        print("  ⏱️  Latency:")
        lat = status["latency"]
        print(f"     Avg       : {lat.get("avg_ms", 0)}ms")
        print(f"     P95       : {lat.get("p95_ms", 0)}ms")
        print(f"     P99       : {lat.get("p99_ms", 0)}ms")
        print()
        cache = status["cache"]
        if cache:
            print(f"  💾 Cache     : Hits={cache.get("hits",0)} Misses={cache.get("misses",0)} Rate={cache.get("hit_rate_pct",0)}%")
        sess = status["sessions"]
        if sess:
            print(f"  👤 Sessions  : Active={sess.get("active_sessions",0)} Total={sess.get("total_sessions",0)}")
        rate = status["rate_limiter"]
        if rate:
            print(f"  🚦 Rate Limit: Allowed={rate.get("total_allowed",0)} Rejected={rate.get("total_rejected",0)}")
        qs = status["queues"]
        if qs:
            for qname, qstats in qs.items():
                sizes = qstats.get("sizes",{})
                print(f"  📬 Queue {qname:10s}: Pending={sizes.get("total",0)} Completed={qstats.get("total_completed",0)}")
        print("=" * 50)
        print()

    elif "--vector-db-status" in args:
        from layers.layer13_persistence.modules.vector_database_platform.vector_db_manager import get_vectordb
        vdb = get_vectordb()
        status = vdb.get_vector_db_status()
        print("\n🧠 VECTOR DATABASE STATUS")
        print("=" * 55)
        print(f"  Overall         : {status["overall"]}")
        print(f"  Dimensions      : {status["dimensions"]}")
        print(f"  Embedding       : {status["embedding_strategy"]}")
        print()
        store = status["storage"]
        print(f"  💾 Storage:")
        print(f"     Records      : {store.get("total_records", 0):,}")
        print(f"     Namespaces   : {store.get("namespaces", {})}")
        print()
        eng = status["embedding"]
        print(f"  🔢 Embedding Engine:")
        print(f"     Vocab Size   : {eng.get("vocab_size", 0):,}")
        print(f"     Generated    : {eng.get("total_generated", 0):,}")
        print(f"     Cache Hit    : {eng.get("cache_hit_rate", 0)}%")
        print()
        mem = status["memory"]
        print(f"  🧠 Long-Term Memory:")
        print(f"     Total        : {mem.get("total", 0):,}")
        print(f"     Short-Term   : {mem.get("short_term", 0):,}")
        print(f"     Long-Term    : {mem.get("long_term", 0):,}")
        print(f"     By Type      : {mem.get("by_type", {})}")
        print()
        dedup = status["deduplication"]
        print(f"  🔍 Deduplication:")
        print(f"     Checked      : {dedup.get("total_checked", 0):,}")
        print(f"     Exact Dupes  : {dedup.get("exact_duplicates", 0):,}")
        print(f"     Near Dupes   : {dedup.get("near_duplicates", 0):,}")
        print()
        print("=" * 55)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--publishing-status" in args:
        from layers.layer07_publishing.modules.multi_platform_engine.publishing_manager import get_publishing
        pub = get_publishing()
        status = pub.get_publishing_status()
        print("\n🚀 MULTI-PLATFORM PUBLISHING STATUS")
        print("=" * 60)
        print(f"  Overall       : {status["overall"]}")
        print(f"  Platforms     : {status["total_platforms"]}")
        print(f"  Supported     : {", ".join(status["supported_platforms"][:8])}...")
        print()
        acc = status["accounts"]
        print(f"  👤 Accounts:")
        print(f"     Total       : {acc["total_accounts"]:,}")
        print(f"     Active      : {acc["active_accounts"]:,}")
        print(f"     Platforms   : {acc["platforms"]}")
        print(f"     Brands      : {acc["brands"]}")
        print()
        eng = status["engine"]
        print(f"  ⚡ Publisher Engine:")
        print(f"     Published   : {eng["total_published"]:,}")
        print(f"     Failed      : {eng["total_failed"]:,}")
        print(f"     Retried     : {eng["total_retried"]:,}")
        print(f"     Handlers    : {eng["registered_handlers"]}")
        print()
        sched = status["scheduler"]
        print(f"  📅 Scheduler:")
        print(f"     Scheduled   : {sched["total_scheduled"]:,}")
        print(f"     Published   : {sched["total_published"]:,}")
        print(f"     Queue Size  : {sched["queue_size"]:,}")
        print()
        ana = status["analytics"]
        dash = ana.get("dashboard", {})
        print(f"  📊 Analytics:")
        print(f"     Posts       : {ana["tracked_posts"]:,}")
        print(f"     Views       : {dash.get("total_views", 0):,}")
        print(f"     Clicks      : {dash.get("total_clicks", 0):,}")
        print(f"     Engagement  : {dash.get("total_engagement", 0):,}")
        print(f"     Affiliate   : {dash.get("total_affiliate_clicks", 0):,}")
        print(f"     Revenue     : ${dash.get("total_affiliate_revenue", 0):,.2f}")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))
    elif "--monitoring-status" in args:
        from layers.layer18_monitoring.modules.monitoring_engine.monitoring_manager import get_monitoring
        mon = get_monitoring()
        status = mon.get_monitoring_status()
        print("\n📡 MONITORING & OBSERVABILITY STATUS")
        print("=" * 60)
        print(f"  Overall       : {status["overall"]}")
        print()
        health = status["health"]
        print(f"  🏥 Health Score: {health.get("score", 0)}/100 ({health.get("status", "unknown")})")
        comps = health.get("components", {})
        for name, comp in comps.items():
            icon = "✅" if comp["status"] == "healthy" else "⚠️" if comp["status"] == "degraded" else "❌"
            print(f"     {icon} {name:15s} : {comp["score"]}/100")
        print()
        sys = status.get("system", {})
        cpu = sys.get("cpu", {})
        mem = sys.get("memory", {})
        disk = sys.get("disk", {})
        print(f"  💻 System Resources:")
        print(f"     CPU         : {cpu.get("percent", 0)}% ({cpu.get("cores", 0)} cores)")
        print(f"     Memory      : {mem.get("percent", 0)}% ({mem.get("used_mb", 0):,}MB / {mem.get("total_mb", 0):,}MB)")
        print(f"     Disk        : {disk.get("percent_used", 0)}% ({disk.get("used_gb", 0):,}GB / {disk.get("total_gb", 0):,}GB)")
        print()
        api = status.get("api", {})
        print(f"  ⚡ API Metrics:")
        print(f"     Requests    : {api.get("total_requests", 0):,}")
        print(f"     Avg Latency : {api.get("avg_latency_ms", 0)}ms")
        print(f"     Error Rate  : {api.get("error_rate_pct", 0)}%")
        print()
        err = status.get("errors", {})
        print(f"  🐛 Error Tracker:")
        print(f"     Total       : {err.get("total_errors", 0):,}")
        print(f"     Groups      : {err.get("unique_error_groups", 0):,}")
        print()
        al = status.get("alerts", {})
        print(f"  🚨 Alerts:")
        print(f"     Rules       : {al.get("rules", 0)}")
        print(f"     Firing      : {al.get("firing", 0)}")
        print(f"     Resolved    : {al.get("resolved", 0)}")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))
    elif "--docker-status" in args:
        from layers.layer21_deployment.modules.docker_engine.docker_deployment_manager import get_docker_manager
        dm = get_docker_manager()
        status = dm.get_deployment_status()
        docker = status["docker"]
        deploy = status["deployment"]
        print("\n🐳 DOCKER DEPLOYMENT STATUS")
        print("=" * 60)
        print(f"  Docker        : {'✅ Available' if docker['docker_available'] else '❌ Not found'}")
        print(f"  Version       : {docker.get('docker_version', 'N/A')}")
        print(f"  Compose       : {'✅ Available' if docker['compose_available'] else '❌ Not found'}")
        print()
        print(f"  📦 Services:")
        print(f"     Expected    : {deploy['total_services']}")
        print(f"     Running     : {deploy['running']}")
        print(f"     Stopped     : {deploy['stopped']}")
        print(f"     Overall     : {deploy['overall']}")
        print()
        containers = deploy.get("containers", {})
        for name, info in containers.items():
            icon = "✅" if info["status"] == "running" else "❌"
            health = "healthy" if info.get("healthy") else "unhealthy"
            print(f"     {icon} {name:15s}: {info['status']:10s} ({health})")
        print()
        print(f"  ⚙️  Config:")
        config = status.get("config", {})
        print(f"     Project     : {config.get('project', 'N/A')}")
        print(f"     Services    : {config.get('services', [])}")
        print(f"     Networks    : {config.get('networks', [])}")
        print()
        history = status.get("deploy_history", [])
        if history:
            print(f"  📜 Recent Deployments: {len(history)}")
            for h in history[-3:]:
                icon = "✅" if h.get("success") else "❌"
                dur = h.get('duration_seconds', 0)
                print(f"     {icon} {h.get('action', 'unknown')} ({dur}s)")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--docker-deploy" in args:
        from layers.layer21_deployment.modules.docker_engine.docker_deployment_manager import get_docker_manager
        dm = get_docker_manager()
        print("\n🚀 Deploying with Docker Compose...")
        result = dm.deploy()
        if result["success"]:
            print(f"✅ Deployed in {result['duration_seconds']}s")
        else:
            print(f"❌ Deployment failed: {result.get('error', 'unknown')}")
        print(json.dumps(result, indent=2, default=str))

    elif "--docker-verify" in args:
        from layers.layer21_deployment.modules.docker_engine.docker_deployment_manager import get_docker_manager
        dm = get_docker_manager()
        print("\n🔍 Verifying Docker deployment...")
        result = dm.verify_deployment()
        print(f"  Docker Available  : {'✅' if result['docker_available'] else '❌'}")
        print(f"  Compose Available : {'✅' if result['compose_available'] else '❌'}")
        print(f"  Running           : {result['containers_running']}/{result['containers_expected']}")
        print(f"  Healthy           : {result['services_healthy']}/{result['containers_expected']}")
        print()
        for check in result.get("checks", []):
            icon = "✅" if check.get("passed") else "❌"
            print(f"  {icon} {check['name']:20s}: {check.get('detail', 'N/A')}")
        print()
        print(f"  Overall: {'✅ PASS' if result['overall'] else '❌ FAIL'}")
        print(json.dumps(result, indent=2, default=str))

    elif "--traffic-status" in args:
        from layers.layer23_website_manager.traffic_manager.traffic_manager import get_traffic_manager
        tm = get_traffic_manager()
        status = tm.get_status()
        sources = status["sources"]
        visitors = status["visitors"]
        pinterest = status["pinterest"]
        search = status["search"]
        campaigns = status["campaigns"]
        alerts = status["alerts"]
        print("\nTRAFFIC MANAGER STATUS (Layer 23 / Module 8)")
        print("=" * 60)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print()
        print(f"  Traffic Sources: {sources['total_sources']} ({sources['unique_sources']} types)")
        print(f"  Visitors       : {visitors['total_visits']} visits, {visitors['unique_visitors']} unique")
        print()
        print(f"  Pinterest:")
        print(f"     Pin Clicks : {pinterest['total_pin_clicks']}")
        print(f"     Saves      : {pinterest['total_saves']}")
        print(f"     Boards     : {pinterest['total_boards']}")
        print()
        print(f"  Search:")
        print(f"     Keywords   : {search['total_keywords']}")
        print(f"     Clicks     : {search['total_clicks']}")
        print(f"     Impressions: {search['total_impressions']}")
        print()
        print(f"  Campaigns     : {campaigns['total_campaigns']} ({campaigns['active']} active)")
        print(f"  Alerts        : {alerts['total_alerts']} ({alerts['unread']} unread, {alerts['critical']} critical)")
        print("=" * 60)
        print(json.dumps(status, indent=2, default=str))
        
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\nSystem: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
        
    elif "--seo-status" in args:
        from layers.layer23_website_manager.seo_richpins_manager.seo_richpins_manager import get_seo_manager
        sm = get_seo_manager()
        status = sm.get_status()
        profiles = status["profiles"]
        print("\nSEO & RICH PINS MANAGER STATUS (Layer 23 / Module 7)")
        print("=" * 60)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print()
        print(f"  Profiles:")
        print(f"     Total      : {profiles['total']}")
        print(f"     Optimized  : {profiles['optimized']}")
        print(f"     Avg Score  : {profiles['avg_seo_score']}/100")
        print()
        print(f"  Keywords     : {status['keywords']['total_generations']} generated")
        print(f"  Meta         : {status['meta']['total_generated']} generated")
        print(f"  Pinterest SEO: {status['pinterest_seo']['total_optimizations']} optimized")
        print(f"  Rich Pins    : {status['rich_pins']['total_rich_pins']} created")
        print(f"  Open Graph   : {status['opengraph']['total_og_tags']} tags")
        print(f"  Twitter      : {status['twitter']['total_cards']} cards")
        print(f"  Schema       : {status['schema']['total_schemas']} schemas")
        print(f"  Sitemap      : {status['sitemap']['total_sitemaps']} sitemaps")
        print(f"  Robots       : {status['robots']['total_robots']} generated")
        print(f"  Validator    : {status['validator']['total_validations']} validated")
        print(f"  Optimizer    : {status['optimizer']['total_analyzed']} analyzed")
        print(f"  Analytics    : {status['analytics']['total_records']} records")
        print("=" * 60)
        print(json.dumps(status, indent=2, default=str))
        
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\nSystem: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
        
    elif "--affiliate-status" in args:
        from layers.layer10_monetization.modules.affiliate_engine.affiliate_engine_manager import get_affiliate_engine
        engine = get_affiliate_engine()
        status = engine.get_full_status()
        aff = status["affiliate"]
        links = status["links"]
        rev = status["revenue"]
        camp = status["campaigns"]
        opt = status["optimizer"]
        print("\n💰 AFFILIATE & MONETIZATION ENGINE STATUS")
        print("=" * 60)
        print(f"  Overall       : {status['overall']}")
        print(f"  Uptime        : {status['uptime_seconds']}s")
        print()
        print(f"  📦 Affiliate Programs:")
        print(f"     Total       : {aff['total_programs']}")
        print(f"     Active      : {aff['active_programs']}")
        print(f"     Links       : {aff['total_links']}")
        print(f"     Clicks      : {aff['total_clicks']:,}")
        print(f"     Conversions : {aff['total_conversions']:,}")
        print(f"     Revenue     : ${aff['total_revenue']:,.2f}")
        print(f"     Conv. Rate  : {aff['overall_conversion_rate']}%")
        print(f"     EPC         : ${aff['overall_epc']}")
        print()
        print(f"  🔗 Link Intelligence:")
        print(f"     Links       : {links['total_links']}")
        print(f"     A/B Tests   : {links['ab_test_links']}")
        print(f"     Clicks      : {links['total_clicks']:,}")
        print()
        print(f"  📊 Revenue Analytics:")
        print(f"     Events      : {rev['total_events']:,}")
        print(f"     Impressions : {rev['total_impressions']:,}")
        print(f"     Clicks      : {rev['total_clicks']:,}")
        print(f"     Conversions : {rev['total_conversions']:,}")
        print(f"     Revenue     : ${rev['total_revenue']:,.2f}")
        print(f"     Commission  : ${rev['total_commission']:,.2f}")
        print(f"     CTR         : {rev['overall_ctr']}%")
        print()
        print(f"  🎯 Campaigns:")
        print(f"     Total       : {camp['total_campaigns']}")
        print(f"     Active      : {camp['active']}")
        print(f"     Paused      : {camp['paused']}")
        print(f"     Completed   : {camp['completed']}")
        print(f"     Niches      : {camp['niches']}")
        print(f"     Revenue     : ${camp['total_revenue']:,.2f}")
        print(f"     Spent       : ${camp['total_spent']:,.2f}")
        print()
        print(f"  🤖 AI Optimizer:")
        print(f"     Niches      : {opt['total_niches']}")
        print(f"     Content     : {opt['total_content_scored']}")
        print(f"     Recs        : {opt['total_recommendations']}")
        cats = opt.get("content_categories", {})
        print(f"     Stars       : {cats.get('star', 0)}")
        print(f"     Performers  : {cats.get('performer', 0)}")
        print(f"     Average     : {cats.get('average', 0)}")
        print(f"     Weak        : {cats.get('underperformer', 0)}")
        print()
        top_niches = opt.get("top_niches", [])
        if top_niches:
            print(f"  🏆 Top Niches   : {', '.join(top_niches)}")
        recs = opt.get("recommendations", [])
        if recs:
            print(f"  💡 Top Recommendations:")
            for r in recs[:3]:
                print(f"     [{r.get('priority', 0)}] {r.get('action', '')}")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--affiliate-summary" in args:
        from layers.layer10_monetization.modules.affiliate_engine.affiliate_engine_manager import get_affiliate_engine
        engine = get_affiliate_engine()
        summary = engine.get_executive_summary()
        print("\n📋 AFFILIATE EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"  Programs       : {summary['total_programs']}")
        print(f"  Links          : {summary['total_links']}")
        print(f"  Campaigns      : {summary['total_campaigns']} ({summary['active_campaigns']} active)")
        print(f"  Revenue        : ${summary['total_revenue']:,.2f}")
        print(f"  Clicks         : {summary['total_clicks']:,}")
        print(f"  Conversions    : {summary['total_conversions']:,}")
        print(f"  Conv. Rate     : {summary['overall_conversion_rate']}%")
        print(f"  EPC            : ${summary['overall_epc']}")
        print(f"  Top Niches     : {', '.join(summary.get('top_niches', []))}")
        print(f"  Recommendations: {summary['recommendations']}")
        print("=" * 50)
        print(json.dumps(summary, indent=2, default=str))

    elif "--niche-intel-status" in args:
        from layers.layer02_research.modules.niche_intelligence.niche_intelligence_manager import get_niche_intelligence
        ni = get_niche_intelligence()
        status = ni.get_full_intelligence()
        research = status["research"]
        products = status["products"]
        keywords = status["keywords"]
        competitors = status["competitors"]
        opps = status["opportunities"]
        preds = status["predictions"]
        rankings = status["rankings"]
        print("\n🧠 NICHE INTELLIGENCE ENGINE STATUS")
        print("=" * 60)
        print(f"  Overall       : {status['overall']}")
        print(f"  Uptime        : {status['uptime_seconds']}s")
        print()
        print(f"  🔍 Research:")
        print(f"     Niches      : {research['total_niches']}")
        print(f"     Avg Score   : {research['avg_score']}")
        print(f"     Very High   : {research['very_high_potential']}")
        print(f"     Keywords    : {research['total_keywords']}")
        print()
        print(f"  📦 Products:")
        print(f"     Total       : {products['total_products']}")
        print(f"     Categories  : {len(products.get('by_category', {}))}")
        print(f"     High Comm.  : {products['high_commission']}")
        print(f"     Recurring   : {products['recurring']}")
        print(f"     Seasonal    : {products['seasonal']}")
        print()
        print(f"  🔑 Keywords:")
        print(f"     Total       : {keywords['total_keywords']}")
        print(f"     Long-tail   : {keywords['long_tail']}")
        print(f"     Questions   : {keywords['questions']}")
        print(f"     Avg Volume  : {keywords['avg_volume']}")
        print(f"     Avg CPC     : ${keywords['avg_cpc']}")
        intents = keywords.get('by_intent', {})
        print(f"     Intent: ", end="")
        print(", ".join(f"{k}={v}" for k, v in intents.items()))
        print()
        print(f"  🏆 Competitors:")
        print(f"     Total       : {competitors['total_competitors']}")
        print(f"     High Threat : {competitors['high_threat']}")
        print(f"     Avg Traffic : {competitors['avg_traffic']:,.0f}")
        print(f"     Avg DA      : {competitors['avg_da']}")
        print()
        print(f"  💡 Opportunities:")
        print(f"     Total       : {opps['total_opportunities']}")
        print(f"     Quick Wins  : {opps['quick_wins']}")
        print(f"     Avg Score   : {opps['avg_score']}")
        print(f"     Est. Traffic: {opps['total_estimated_traffic']:,}")
        print(f"     Est. Revenue: ${opps['total_estimated_revenue']:,.2f}")
        print()
        print(f"  💰 Revenue Predictions:")
        print(f"     Monthly     : ${preds['total_predicted_monthly']:,.2f}")
        print(f"     Annual      : ${preds['total_predicted_annual']:,.2f}")
        print()
        if rankings:
            print(f"  🏅 Niche Rankings:")
            for i, r in enumerate(rankings[:5], 1):
                print(f"     {i}. {r['niche']:25s} Score={r['score']:.1f}  "
                      f"Potential={r['monetization_potential']}")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--niche-intel-summary" in args:
        from layers.layer02_research.modules.niche_intelligence.niche_intelligence_manager import get_niche_intelligence
        ni = get_niche_intelligence()
        summary = ni.get_executive_summary()
        print("\n📋 NICHE INTELLIGENCE EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"  Niches        : {summary['total_niches']}")
        print(f"  Products      : {summary['total_products']}")
        print(f"  Keywords      : {summary['total_keywords']}")
        print(f"  Competitors   : {summary['total_competitors']}")
        print(f"  Predicted/Mo  : ${summary['predicted_monthly_revenue']:,.2f}")
        print(f"  Predicted/Yr  : ${summary['predicted_annual_revenue']:,.2f}")
        print(f"  Top Niches    : {', '.join(summary['top_niches'])}")
        print("=" * 50)
        print(json.dumps(summary, indent=2, default=str))

    elif "--empire-status" in args:
        from layers.layer07_publishing.modules.empire_engine.empire_engine_manager import get_empire_engine
        emp = get_empire_engine()
        status = emp.get_empire_status()
        reg = status["registry"]
        sched = status["scheduler"]
        health = status["health"]
        scaling = status["scaling"]
        sync = status["sync"]
        print("\n👑 EMPIRE AUTOMATION ENGINE STATUS")
        print("=" * 60)
        print(f"  Overall       : {status['overall']}")
        print(f"  Uptime        : {status['uptime_seconds']}s")
        print()
        print(f"  📋 Account Registry:")
        print(f"     Total       : {reg['total_accounts']}")
        print(f"     Active      : {reg['active']}")
        print(f"     Paused      : {reg['paused']}")
        print(f"     Banned      : {reg['banned']}")
        print(f"     Platforms   : {reg['platforms_count']}")
        print(f"     Niches      : {reg['niches_count']}")
        print(f"     Regions     : {reg['regions_count']}")
        print(f"     Followers   : {reg['total_followers']:,}")
        print()
        platforms = reg.get("by_platform", {})
        if platforms:
            print(f"  📱 By Platform:")
            for p, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True)[:8]:
                print(f"     {p:15s}: {count}")
        print()
        print(f"  📅 Publishing Queue:")
        print(f"     Queued      : {sched['queued']}")
        print(f"     Published   : {sched['published']}")
        print(f"     Failed      : {sched['failed']}")
        print(f"     Ready Now   : {sched['ready_now']}")
        print(f"     Retry       : {sched['retry_pending']}")
        print()
        print(f"  🔄 Cross-Platform Sync:")
        print(f"     Rules       : {sync['active_rules']}")
        print(f"     Events      : {sync['total_events']}")
        print(f"     Pending     : {sync['pending']}")
        print(f"     Completed   : {sync['completed']}")
        print()
        print(f"  🏥 Account Health:")
        print(f"     Checked     : {health['total_checked']}")
        print(f"     Healthy     : {health['healthy']}")
        print(f"     Degraded    : {health['degraded']}")
        print(f"     Unhealthy   : {health['unhealthy']}")
        print(f"     Shadow Ban  : {health['shadow_ban_suspects']}")
        print(f"     Avg Score   : {health['avg_health_score']}")
        print()
        tier = scaling["current_tier"]
        print(f"  📈 Scaling:")
        print(f"     Tier        : {tier['name']}")
        print(f"     Accounts    : {scaling['current_accounts']}")
        print(f"     Workers     : {tier['workers']}")
        print(f"     DB Pool     : {tier['db_pool']}")
        print(f"     Cache       : {tier['cache_mb']}MB")
        next_tier = scaling.get("next_tier")
        if next_tier:
            print(f"     Next Tier   : {next_tier['name']} ({next_tier['accounts']})")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--empire-summary" in args:
        from layers.layer07_publishing.modules.empire_engine.empire_engine_manager import get_empire_engine
        emp = get_empire_engine()
        summary = emp.get_executive_summary()
        print("\n📋 EMPIRE EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"  Accounts      : {summary['total_accounts']} ({summary['active_accounts']} active)")
        print(f"  Platforms      : {summary['platforms']}")
        print(f"  Niches         : {summary['niches']}")
        print(f"  Regions        : {summary['regions']}")
        print(f"  Followers      : {summary['total_followers']:,}")
        print(f"  Queued Posts   : {summary['queued_posts']}")
        print(f"  Published      : {summary['published_today']}")
        print(f"  Healthy        : {summary['healthy_accounts']}")
        print(f"  Unhealthy      : {summary['unhealthy_accounts']}")
        print(f"  Current Tier   : {summary['current_tier']}")
        print(f"  Scale To       : {summary['can_scale_to']}")
        print("=" * 50)
        print(json.dumps(summary, indent=2, default=str))

    elif "--self-improve-status" in args:
        from layers.layer09_learning.modules.self_improvement_engine.self_improvement_manager import get_self_improvement
        si = get_self_improvement()
        status = si.get_full_status()
        perf = status["performance"]
        mistakes = status["mistakes"]
        strategy = status["strategy"]
        prompts = status["prompts"]
        ab = status["ab_testing"]
        knowledge = status["knowledge"]
        actions = si._generate_improvement_actions()
        print("\n🧠 SELF-IMPROVEMENT & STRATEGY ENGINE STATUS")
        print("=" * 60)
        print(f"  Overall       : {status['overall']}")
        print(f"  Uptime        : {status['uptime_seconds']}s")
        print()
        print(f"  📊 Performance:")
        print(f"     Records     : {perf['total_records']}")
        print(f"     Avg Score   : {perf['avg_performance_score']}")
        print(f"     Revenue     : ${perf['total_revenue']:,.2f}")
        print(f"     Platforms   : {perf['platforms']}")
        print()
        print(f"  🔍 Mistake Detection:")
        print(f"     Patterns    : {mistakes['total_patterns']}")
        print(f"     Active      : {mistakes['active']}")
        print(f"     Resolved    : {mistakes['resolved']}")
        sev = mistakes.get("by_severity", {})
        print(f"     Critical    : {sev.get('critical', 0)}")
        print(f"     High        : {sev.get('high', 0)}")
        print()
        print(f"  📋 Strategy:")
        print(f"     Recommendations: {strategy['total_recommendations']}")
        print(f"     Pending     : {strategy['pending']}")
        print(f"     Applied     : {strategy['applied']}")
        print(f"     Versions    : {strategy['total_versions']}")
        ver = strategy.get("current_version")
        if ver:
            print(f"     Current     : v{ver.get('version', '?')} ({ver.get('name', '')})")
        print()
        print(f"  🤖 Prompt Optimizer:")
        print(f"     Prompts     : {prompts['total_prompts']}")
        print(f"     Active      : {prompts['active']}")
        print(f"     Promoted    : {prompts['promoted']}")
        print(f"     Retired     : {prompts['retired']}")
        print(f"     Avg Score   : {prompts['avg_score']}")
        print()
        print(f"  🧪 A/B Testing:")
        print(f"     Experiments : {ab['total_experiments']}")
        print(f"     Running     : {ab['running']}")
        print(f"     Completed   : {ab['completed']}")
        print(f"     Winners     : {ab['total_winners']}")
        print()
        print(f"  📚 Knowledge:")
        print(f"     Entries     : {knowledge['total_entries']}")
        print(f"     Active      : {knowledge['active']}")
        print(f"     Retired     : {knowledge['retired']}")
        print(f"     Avg Conf.   : {knowledge['avg_confidence']}")
        print()
        print(f"  🎯 Improvement Actions:")
        for a in actions:
            print(f"     {a}")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--self-improve-summary" in args:
        from layers.layer09_learning.modules.self_improvement_engine.self_improvement_manager import get_self_improvement
        si = get_self_improvement()
        summary = si.get_executive_summary()
        print("\n📋 SELF-IMPROVEMENT EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"  Performance Records: {summary['total_performance_records']}")
        print(f"  Total Revenue      : ${summary['total_revenue']:,.2f}")
        print(f"  Active Mistakes    : {summary['active_mistakes']}")
        print(f"  Strategy Recs      : {summary['strategy_recommendations']}")
        print(f"  Active Prompts     : {summary['active_prompts']}")
        print(f"  Running Experiments: {summary['running_experiments']}")
        print(f"  Knowledge Entries  : {summary['knowledge_entries']}")
        print()
        print(f"  Actions:")
        for a in summary.get("improvement_actions", []):
            print(f"    {a}")
        print("=" * 50)
        print(json.dumps(summary, indent=2, default=str))

    elif "--bi-status" in args:
        from layers.layer19_analytics_engine.modules.bi_platform.bi_manager import get_bi_manager
        bi = get_bi_manager()
        status = bi.get_full_bi_status()
        ceo = status["ceo"]
        niche = status["niche"]
        platform = status["platform"]
        ai = status["ai"]
        empire = status["empire"]
        alerts = status["alerts"]
        forecast = status["forecasting"]
        api = status["api"]
        print("\n📊 ENTERPRISE ANALYTICS & BUSINESS INTELLIGENCE")
        print("=" * 60)
        print(f"  Overall       : {status['overall']}")
        print(f"  Uptime        : {status['uptime_seconds']}s")
        print()
        print(f"  👔 CEO Dashboard:")
        print(f"     Revenue     : ${ceo.get('total_revenue', 0):,.2f}")
        print(f"     Profit      : ${ceo.get('total_profit', 0):,.2f}")
        print(f"     Accounts    : {ceo.get('total_accounts', 0)}")
        print(f"     AI Health   : {ceo.get('ai_health', 0)}")
        growth = ceo.get("growth", {})
        if growth:
            print(f"     Daily Growth: {growth.get('daily_growth', 0)}%")
            print(f"     Weekly      : {growth.get('weekly_growth', 0)}%")
        print()
        print(f"  💰 Revenue Forecast:")
        f30 = forecast.get("forecasts", {}).get("30day", {})
        f90 = forecast.get("forecasts", {}).get("90day", {})
        f1y = forecast.get("forecasts", {}).get("1year", {})
        if f30:
            print(f"     30-Day      : ${f30.get('total_revenue', 0):,.2f}")
        if f90:
            print(f"     90-Day      : ${f90.get('total_revenue', 0):,.2f}")
        if f1y:
            print(f"     1-Year      : ${f1y.get('total_revenue', 0):,.2f}")
        roi = forecast.get("roi", {})
        if roi:
            print(f"     ROI (30d)   : {roi.get('roi_30day', 0)}%")
            print(f"     Payback     : {roi.get('payback_days', 0)} days")
        print()
        print(f"  🎯 Niche Dashboard:")
        print(f"     Niches      : {niche['total_niches']}")
        print(f"     Revenue     : ${niche['total_revenue']:,.2f}")
        print(f"     Growing     : {niche.get('growing', 0)}")
        print(f"     Declining   : {niche.get('declining', 0)}")
        print()
        print(f"  📱 Platform Dashboard:")
        print(f"     Platforms   : {platform['total_platforms']}")
        print(f"     Total Reach : {platform['total_reach']:,}")
        print(f"     Revenue     : ${platform['total_revenue']:,.2f}")
        print()
        print(f"  🤖 AI Dashboard:")
        ai_cur = ai.get("current", {})
        print(f"     Accuracy    : {ai_cur.get('accuracy', 0)}%")
        print(f"     Quality     : {ai_cur.get('quality', 0)}%")
        print(f"     Prompt OK   : {ai_cur.get('prompt_success', 0)}%")
        print(f"     RAG         : {ai_cur.get('rag_accuracy', 0)}%")
        print(f"     Health      : {ai_cur.get('overall_health', 0)}")
        print()
        emp_cur = empire.get("current", {})
        print(f"  👑 Empire Dashboard:")
        print(f"     Accounts    : {emp_cur.get('total_accounts', 0)}")
        print(f"     Healthy     : {emp_cur.get('healthy_accounts', 0)} ({emp_cur.get('health_rate', 0)}%)")
        print(f"     Shadow Ban  : {emp_cur.get('shadow_ban_alerts', 0)}")
        print(f"     Published   : {emp_cur.get('published_today', 0)}")
        print(f"     Failed      : {emp_cur.get('failed_posts', 0)}")
        print()
        print(f"  🚨 Alert Center:")
        print(f"     Active      : {alerts['active']}")
        print(f"     Critical    : {alerts['critical_active']}")
        print(f"     Resolved    : {alerts['resolved']}")
        sev = alerts.get("by_severity", {})
        print(f"     Emergency   : {sev.get('emergency', 0)}")
        print()
        print(f"  📡 API:")
        print(f"     Endpoints   : {api['total_endpoints']}")
        print(f"     Requests    : {api['total_requests']}")
        print(f"     Avg Latency : {api['avg_latency']}ms")
        print("=" * 60)
        print()
        print(json.dumps(status, indent=2, default=str))

    elif "--bi-summary" in args:
        from layers.layer19_analytics_engine.modules.bi_platform.bi_manager import get_bi_manager
        bi = get_bi_manager()
        summary = bi.get_executive_summary()
        print("\n📋 BUSINESS INTELLIGENCE EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"  Revenue       : ${summary['total_revenue']:,.2f}")
        print(f"  Profit        : ${summary['total_profit']:,.2f}")
        print(f"  Accounts      : {summary['total_accounts']} ({summary['active_accounts']} active)")
        print(f"  Niches        : {summary['total_niches']}")
        print(f"  Platforms     : {summary['total_platforms']}")
        print(f"  AI Health     : {summary['ai_health']}")
        print(f"  Empire Health : {summary['empire_health_rate']}%")
        print(f"  Alerts        : {summary['active_alerts']} ({summary['critical_alerts']} critical)")
        print("=" * 50)
        print(json.dumps(summary, indent=2, default=str))

        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")

    elif "--mapping-status" in args:
        from layers.layer23_website_manager.content_mapping_engine.content_mapping_engine import get_mapping_engine
        me = get_mapping_engine()
        status = me.get_status()
        mappings = status["mappings"]
        print("\nCONTENT MAPPING ENGINE STATUS (Layer 23 / Module 5)")
        print("=" * 60)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print()
        print(f"  Mappings:")
        print(f"     Total      : {mappings['total']}")
        print(f"     Validated  : {mappings['validated']}")
        print(f"     Pending    : {mappings['pending']}")
        print(f"     By Niche   : {mappings['by_niche']}")
        print()
        print(f"  Classifier       : {status['classifier']['total_classified']} classified")
        print(f"  Website Mapper   : {status['website_mapper']['total_mappings']} mappings")
        print(f"  Account Mapper   : {status['account_mapper']['total_mappings']} mappings")
        print(f"  Board Mapper     : {status['board_mapper']['total_mappings']} mappings")
        print(f"  Pin Strategy     : {status['pin_strategy']['total_strategies']} strategies")
        print(f"  Affiliate Mapper : {status['affiliate_mapper']['total_mappings']} mappings")
        print(f"  SEO Mapper       : {status['seo_mapper']['total_profiles']} profiles")
        print(f"  Image Mapper     : {status['image_mapper']['total_mappings']} mappings")
        print(f"  Scheduler        : {status['scheduling_mapper']['total_scheduled']} scheduled")
        print(f"  Validator        : {status['validator']['total_validations']} validations")
        print(f"  Relationship     : {status['relationship_engine']['total_relationships']} relationships")
        print(f"  Recommendations  : {status['recommendation_engine']['total_recommendations']} recommendations")
        print("=" * 60)
        print(json.dumps(status, indent=2, default=str))
        
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\nSystem: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
        
    elif "--pin-status" in args:
        from layers.layer23_website_manager.pinterest_pin_manager.pinterest_pin_manager import get_pin_manager
        pm = get_pin_manager()
        status = pm.get_status()
        pins = status["pins"]
        health = status["health"]
        scheduler = status["scheduler"]
        publisher = status["publisher"]
        queue = status["queue"]
        print("\nPINTEREST PIN MANAGER STATUS (Layer 23 / Module 4)")
        print("=" * 60)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print()
        print(f"  Pins:")
        print(f"     Total      : {pins['total_pins']}")
        print(f"     Published  : {pins['published']}")
        print(f"     Draft      : {pins['draft']}")
        print(f"     Scheduled  : {pins['scheduled']}")
        print(f"     Failed     : {pins['failed']}")
        print()
        print(f"  Health:")
        print(f"     Score      : {health['score']}/100")
        print(f"     Healthy    : {health['healthy']}")
        print(f"     Degraded   : {health['degraded']}")
        print(f"     Critical   : {health['critical']}")
        print(f"     Issues     : {health['issues']}")
        print()
        print(f"  Scheduler: {scheduler['total_scheduled']} scheduled")
        print(f"  Publisher: {publisher['total_published']} published | {publisher['success_rate']}% success")
        print(f"  Queue     : {queue['queue_size']} queued")
        print(f"  Analytics : {status['analytics']['tracked_pins']} tracked")
        print(f"  SEO       : {status['seo']['total_optimizations']} optimizations")
        print(f"  Optimizer : {status['optimizer']['total_analyzed']} analyzed")
        print("=" * 60)
        print(json.dumps(status, indent=2, default=str))
        
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\nSystem: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
        
    elif "--board-status" in args:
        from layers.layer23_website_manager.pinterest_board_manager.pinterest_board_manager import get_board_manager
        bm = get_board_manager()
        status = bm.get_status()
        boards = status["boards"]
        health = status["health"]
        print("\n📋 PINTEREST BOARD MANAGER STATUS (Layer 23 / Module 3)")
        print("=" * 60)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print()
        print(f"  📊 Boards:")
        print(f"     Total      : {boards['total_boards']}")
        print(f"     Total Pins : {boards['total_pins']}")
        print(f"     Empty      : {boards['empty_boards']}")
        print(f"     By Status  : {boards['by_status']}")
        print(f"     By Niche   : {boards['by_niche']}")
        print()
        print(f"  🏥 Health:")
        print(f"     Score      : {health['overall_score']}/100")
        print(f"     Healthy    : {health['healthy']}")
        print(f"     Degraded   : {health['degraded']}")
        print(f"     Critical   : {health['critical']}")
        print(f"     Issues     : {health['issues']}")
        print()
        print(f"  🔍 SEO: {status['seo']['total_optimizations']} optimizations")
        print(f"  📈 Analytics: {status['analytics']['tracked_boards']} boards tracked")
        print(f"  💡 Recommendations: {status['recommendations']['total_recommendations']}")
        print("=" * 60)
        print(json.dumps(status, indent=2, default=str))

        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")

    elif "--pinterest-status" in args:
        from layers.layer23_website_manager.pinterest_account_manager.pinterest_account_manager import get_pinterest_manager
        pm = get_pinterest_manager()
        status = pm.get_status()
        accounts = status["accounts"]
        health = status["health"]
        auth = status["authentication"]
        print("\n📌 PINTEREST ACCOUNT MANAGER STATUS (Layer 23 / Module 2)")
        print("=" * 60)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print()
        print(f"  👤 Accounts:")
        print(f"     Total      : {accounts['total']}/{accounts['max']}")
        print(f"     Available  : {accounts['available_slots']} slots")
        print(f"     Healthy    : {accounts['healthy']}")
        print(f"     Unhealthy  : {accounts['unhealthy']}")
        print(f"     By Status  : {accounts['by_status']}")
        print(f"     By Niche   : {accounts['by_niche']}")
        print()
        print(f"  🏥 Health:")
        print(f"     Score      : {health['overall_score']}/100")
        print(f"     Healthy    : {health['healthy']}")
        print(f"     Degraded   : {health['degraded']}")
        print(f"     Critical   : {health['critical']}")
        print()
        print(f"  🔑 Authentication:")
        print(f"     Tokens     : {auth['tokens']}")
        print(f"     Healthy    : {auth['healthy']}")
        print(f"     Expiring   : {auth['expiring_soon']}")
        print(f"     Expired    : {auth['expired']}")
        print("=" * 60)
        print(json.dumps(status, indent=2, default=str))

        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")

    elif "--website-status" in args:
        from layers.layer23_website_manager.website_manager import get_website
        wm = get_website()
        status = wm.get_status()
        config = status["configuration"]
        articles = status["articles"]
        health = status["health"]
        print("\n🌐 WEBSITE MANAGER STATUS (Layer 23)")
        print("=" * 55)
        print(f"  Version       : {status['version']}")
        print(f"  Overall       : {status['overall']}")
        print(f"  Domain        : {config['domain']}")
        print(f"  Site Name     : {config['site_name']}")
        print(f"  Language      : {config['language']}")
        print()
        print(f"  📄 Articles:")
        print(f"     Total      : {articles['total_articles']}")
        print(f"     Published  : {articles['by_status'].get('published', 0)}")
        print(f"     Draft      : {articles['by_status'].get('draft', 0)}")
        print(f"     Scheduled  : {articles['by_status'].get('scheduled', 0)}")
        print()
        print(f"  🏥 Health:")
        print(f"     Overall    : {health['overall_score']}/100")
        print(f"     Content    : {health['content_health']}/100")
        print(f"     Config     : {health['config_health']}/100")
        print(f"     Issues     : {health['issues']}")
        print()
        print(f"  🔗 URL Manager:")
        url = status["url_manager"]
        print(f"     Slugs      : {url['existing_slugs']}")
        print(f"     Redirects  : {url['redirects']}")
        print(f"     Canonicals : {url['canonical_urls']}")
        print()
        print(f"  💾 Media:")
        med = status["media"]
        print(f"     Assets     : {med['total_assets']}")
        print(f"     Size       : {med['total_size_mb']}MB")
        print()
        print(f"  🔍 SEO:")
        seo = status["seo"]
        print(f"     Sitemap    : {seo['sitemap_urls']} URLs")
        print(f"     Schema     : {seo['structured_data_entries']} entries")
        print(f"     Meta OK    : {'Yes' if seo['meta_defaults']['meta_title'] else 'No'}")
        print("=" * 55)
        print(json.dumps(status, indent=2, default=str))

        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")

    else:
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
