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

    else:
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
