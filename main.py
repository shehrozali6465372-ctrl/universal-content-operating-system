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
    started = time.time()
    loaded = []
    errors = []
    for name, module_path in LAYER_MAP:
        try:
            __import__(module_path)
            loaded.append(name)
        except Exception as exc:
            errors.append({"layer": name, "error": str(exc)})
    return {
        "version": VERSION,
        "expected_layers": len(LAYER_MAP),
        "loaded_layers": len(loaded),
        "layers": loaded,
        "errors": errors,
        "boot_time_seconds": round(time.time() - started, 3),
    }

def generate_content(topic: str, platform: str = "facebook", tone: str = "professional",
                     style: str = "educational", include_image: bool = True,
                     account_id: Optional[str] = None) -> Dict[str, Any]:
    from layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane import ControlPlane
    return ControlPlane().execute(topic=topic, platform=platform, account_id=account_id,
                                  tone=tone, style=style, include_image=include_image)

def status() -> Dict[str, Any]:
    layer_dirs = sorted(glob.glob("layers/layer*/"))
    return {
        "version": VERSION,
        "total_layers": len(LAYER_MAP),
        "architectural_layers": len(LAYER_MAP),
        "layer_directories": len(layer_dirs),
        "python_files": sum(len(glob.glob(f"{d}**/*.py", recursive=True)) for d in layer_dirs),
        "layers": [os.path.basename(d.rstrip("/\")) for d in layer_dirs],
    }

def integration_status() -> Dict[str, Any]:
    from layers.layer14_enterprise_integration.modules.real_integrations import IntegrationConfig
    config = IntegrationConfig.from_env()
    return {"version": VERSION, "real_only": True, "providers": config.status()}

def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--status" in args:
        print(json.dumps(status(), indent=2, default=str)); return 0
    if "--boot" in args:
        print(json.dumps(boot(), indent=2, default=str)); return 0
    if "--integration-status" in args:
        print(json.dumps(integration_status(), indent=2, default=str)); return 0
    if "--stats" in args:
        print(json.dumps({"version": VERSION, "layers": len(LAYER_MAP)}, indent=2)); return 0
    if "--generate" in args or "--topic" in args:
        flag = "--topic" if "--topic" in args else "--generate"
        idx = args.index(flag)
        topic = args[idx + 1] if idx + 1 < len(args) else "artificial intelligence"
        platform, tone, style = "facebook", "professional", "educational"
        include_image = "--no-image" not in args
        account_id = None
        for option in ("--platform", "--tone", "--style", "--account-id"):
            if option in args:
                i = args.index(option); value = args[i + 1] if i + 1 < len(args) else ""
                if option == "--platform": platform = value
                elif option == "--tone": tone = value
                elif option == "--style": style = value
                else: account_id = value
        try:
            result = generate_content(topic, platform, tone, style, include_image, account_id)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, indent=2)); return 1
        print(json.dumps(result, indent=2, default=str)); return 0
    result = boot()
    print(f"Boot complete: {result['loaded_layers']}/{result['expected_layers']} layers loaded")
    print(json.dumps({"name": "Universal Content Operating System", "version": VERSION,
                      "commands": ["--boot", "--status", "--integration-status", "--stats",
                                   "--generate <topic> [--account-id <id>]"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
