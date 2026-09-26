"""Universal Content Operating System — canonical entry point."""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from typing import Any, Dict, Optional

VERSION = "6.0.0"
LAYER_MAP = [
    ("Layer 1 — Core", "layers.layer01_core"), ("Layer 2 — Research", "layers.layer02_research"),
    ("Layer 3 — Intelligence", "layers.layer03_intelligence"), ("Layer 4 — Writing", "layers.layer04_writing"),
    ("Layer 5 — Image", "layers.layer05_image"), ("Layer 6 — Quality", "layers.layer06_quality"),
    ("Layer 7 — Publishing", "layers.layer07_publishing"), ("Layer 8 — Analytics", "layers.layer08_analytics"),
    ("Layer 9 — Learning", "layers.layer09_learning"), ("Layer 10 — Monetization", "layers.layer10_monetization"),
    ("Layer 11 — Async Runtime", "layers.layer11_async_runtime"), ("Layer 12 — AI Foundation", "layers.layer12_ai_foundation"),
    ("Layer 13 — Persistence", "layers.layer13_persistence"), ("Layer 14 — Integration", "layers.layer14_enterprise_integration"),
    ("Layer 15 — Async Runtime", "layers.layer15_async_runtime"), ("Layer 16 — Database", "layers.layer16_database_engineering"),
    ("Layer 17 — Security", "layers.layer17_security"), ("Layer 18 — Monitoring", "layers.layer18_monitoring"),
    ("Layer 19 — Analytics Engine", "layers.layer19_analytics_engine"), ("Layer 20 — Image Pipeline", "layers.layer20_image_pipeline"),
    ("Layer 21 — Deployment", "layers.layer21_deployment"), ("Layer 22 — Documentation", "layers.layer22_documentation"),
    ("Layer 23 — Website Manager", "layers.layer23_website_manager"),
]

def boot() -> Dict[str, Any]:
    started = time.time(); loaded = []; errors = []
    for name, module_path in LAYER_MAP:
        try:
            __import__(module_path); loaded.append(name)
        except Exception as exc:
            errors.append({"layer": name, "error": str(exc)})
    return {"version": VERSION, "expected_layers": len(LAYER_MAP), "loaded_layers": len(loaded),
            "layers": loaded, "errors": errors, "boot_time_seconds": round(time.time() - started, 3)}

def generate_content(topic: str, platform: str = "facebook", tone: str = "professional",
                     style: str = "educational", include_image: bool = True,
                     account_id: Optional[str] = None) -> Dict[str, Any]:
    from layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane import ControlPlane
    return ControlPlane().execute(topic=topic, platform=platform, account_id=account_id,
                                  tone=tone, style=style, include_image=include_image)

def status() -> Dict[str, Any]:
    layer_dirs = sorted(glob.glob("layers/layer*/"))
    return {"version": VERSION, "total_layers": len(LAYER_MAP), "architectural_layers": len(LAYER_MAP),
            "layer_directories": len(layer_dirs),
            "python_files": sum(len(glob.glob(f"{d}**/*.py", recursive=True)) for d in layer_dirs),
            "layers": [os.path.basename(d.rstrip("/\\")) for d in layer_dirs]}

def integration_status() -> Dict[str, Any]:
    from layers.layer14_enterprise_integration.modules.real_integrations import IntegrationConfig
    config = IntegrationConfig.from_env()
    return {"version": VERSION, "real_only": True, "providers": config.status()}

def history(limit: int = 10, platform: Optional[str] = None) -> Dict[str, Any]:
    from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
    persist = PipelinePersistence()
    try:
        rows = persist.get_content_history(platform=platform, limit=limit)
        return {"history": rows, "count": len(rows), "platform": platform, "platform_filter": platform}
    finally:
        persist.close()

def analytics() -> Dict[str, Any]:
    from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
    persist = PipelinePersistence()
    try:
        data = persist.get_analytics_summary()
        return {"analytics": data, "total_metrics": len(data)}
    finally:
        persist.close()

def stats() -> Dict[str, Any]:
    db = {}
    try:
        from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
        p = PipelinePersistence(); db = p.get_db_stats(); p.close()
    except Exception as exc:
        db = {"error": str(exc)}
    return {"version": VERSION, "layers": len(LAYER_MAP), "database": db}

def subsystem_status(name: str) -> Dict[str, Any]:
    return {"subsystem": name, "status": "available", "verified": False,
            "note": "Module availability only; external services/credentials are not claimed."}

def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--status" in args:
        print(json.dumps(status(), indent=2, default=str)); return 0
    if "--boot" in args:
        result = boot(); print(json.dumps(result, indent=2, default=str)); return 0
    if "--integration-status" in args:
        print(json.dumps(integration_status(), indent=2, default=str)); return 0
    if "--stats" in args:
        print(json.dumps(stats(), indent=2, default=str)); return 0
    subsystem_commands = {
        "--db-status": "database", "--redis-status": "redis", "--vector-db-status": "vector_db",
        "--publishing-status": "publishing", "--monitoring-status": "monitoring",
        "--docker-status": "docker", "--affiliate-status": "affiliate", "--niche-intel-status": "niche_intelligence",
        "--empire-status": "empire", "--self-improve-status": "self_improvement", "--bi-status": "business_intelligence",
    }
    for flag, name in subsystem_commands.items():
        if flag in args:
            print(json.dumps(subsystem_status(name), indent=2)); return 0
    if "--generate" in args or "--topic" in args:
        flag = "--topic" if "--topic" in args else "--generate"; idx = args.index(flag)
        topic = args[idx + 1] if idx + 1 < len(args) else "artificial intelligence"
        platform = "facebook"; tone = "professional"; style = "educational"; include_image = "--no-image" not in args
        account_id = None
        for option, default in (("--platform", platform), ("--tone", tone), ("--style", style), ("--account-id", None)):
            if option in args:
                i = args.index(option); value = args[i + 1] if i + 1 < len(args) else default
                if option == "--platform": platform = value
                elif option == "--tone": tone = value
                elif option == "--style": style = value
                else: account_id = value
        try:
            print(json.dumps(generate_content(topic, platform, tone, style, include_image, account_id), indent=2, default=str)); return 0
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, indent=2)); return 1
    if "--history" in args:
        limit = 10; platform = None
        if "--limit" in args:
            i = args.index("--limit"); limit = int(args[i + 1])
        if "--platform" in args:
            i = args.index("--platform"); platform = args[i + 1]
        print(json.dumps(history(limit, platform), indent=2, default=str)); return 0
    if "--analytics" in args:
        print(json.dumps(analytics(), indent=2, default=str)); return 0
    if "--api" in args:
        from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway
        port = 8000
        if "--port" in args:
            i = args.index("--port"); port = int(args[i + 1])
        host = os.environ.get("APP_HOST", "127.0.0.1")
        gateway = APIGateway(host=host, port=port)
        gateway.start()
        print(f"UCOS API listening on http://{host}:{port}")
        try:
            while gateway.is_running(): time.sleep(1)
        except KeyboardInterrupt: gateway.stop()
        return 0
    result = boot()
    print(f"Boot complete: {result['loaded_layers']}/{result['expected_layers']} layers loaded")
    print(json.dumps({"name": "Universal Content Operating System", "version": VERSION,
                      "commands": ["--boot", "--status", "--integration-status", "--stats", "--db-status", "--redis-status",
                                   "--vector-db-status", "--publishing-status", "--monitoring-status",
                                   "--docker-status", "--affiliate-status", "--niche-intel-status",
                                   "--empire-status", "--self-improve-status", "--bi-status",
                                   "--generate <topic> [--account-id <id>]", "--history", "--analytics", "--api"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
