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
        self.version = "5.2.0"
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
        "version": "5.2.0",
        "total_layers": len(layer_dirs),
        "total_python_files": total_files,
        "layers": [os.path.basename(d.rstrip("/")) for d in layer_dirs],
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

    else:
        boot = AIOSBoot()
        result = boot.boot()
        print(f"\n📊 System: {result['version']} | {result['layers_loaded']} layers | {result['boot_time_seconds']}s")
