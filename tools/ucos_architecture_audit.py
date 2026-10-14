#!/usr/bin/env python3
"""Evidence-first UCOS layer/agent dependency audit. This tool never deletes code."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("layers", "agents", "tools", "scripts", "tests")
TEXT_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg"}
MODEL_PATH_TERMS = (
    "model", "router", "provider", "llm", "openai", "gemini", "deepseek",
    "huggingface", "puter", "tavily", "gdelt", "inference", "embedding",
)
LAYER_RE = re.compile(r"^layer\d{1,2}_")


def repo_relative(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def module_name(path: Path, root: Path = ROOT) -> str:
    rel = path.relative_to(root).with_suffix("")
    if rel.name == "__init__":
        rel = rel.parent
    return ".".join(rel.parts)


def production_python_paths(root: Path) -> list[Path]:
    files: set[Path] = set()
    for folder in SOURCE_ROOTS:
        base = root / folder
        if base.is_dir():
            files.update(p for p in base.rglob("*.py") if p.is_file())
    main = root / "main.py"
    if main.is_file():
        files.add(main)
    return sorted(files)


def layer_dirs(root: Path) -> list[Path]:
    base = root / "layers"
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.iterdir()
        if p.is_dir() and LAYER_RE.match(p.name)
    )


def _absolute_import_targets(node: ast.AST, current_module: str, path: Path) -> set[str]:
    targets: set[str] = set()
    if isinstance(node, ast.Import):
        for alias in node.names:
            targets.add(alias.name)
    elif isinstance(node, ast.ImportFrom):
        if node.level:
            is_package = path.name == "__init__.py"
            package = current_module if is_package else current_module.rpartition(".")[0]
            parts = package.split(".") if package else []
            for _ in range(max(0, node.level - 1)):
                if parts:
                    parts.pop()
            base = ".".join(parts)
            if node.module:
                base = f"{base}.{node.module}" if base else node.module
        else:
            base = node.module or ""
        if base:
            targets.add(base)
        for alias in node.names:
            if alias.name != "*":
                targets.add(f"{base}.{alias.name}" if base else alias.name)
    return targets


def build_report(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    files = production_python_paths(root)
    module_to_path: dict[str, Path] = {}
    parsed: dict[Path, ast.AST] = {}
    syntax_errors: list[dict[str, str]] = []
    for path in files:
        name = module_name(path, root)
        module_to_path[name] = path
        try:
            parsed[path] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            syntax_errors.append({
                "path": repo_relative(path, root),
                "error": f"{type(exc).__name__}: {exc}",
            })

    importers: dict[Path, set[str]] = defaultdict(set)
    import_edges: list[dict[str, str]] = []
    for source, tree in parsed.items():
        src_mod = module_name(source, root)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for target in _absolute_import_targets(node, src_mod, source):
                dest = module_to_path.get(target)
                if dest is None:
                    continue
                importers[dest].add(repo_relative(source, root))
                import_edges.append({
                    "from": repo_relative(source, root),
                    "to": repo_relative(dest, root),
                    "line": str(getattr(node, "lineno", "")),
                })

    manifest_path = root / "agents" / "manifest.json"
    agents: list[dict[str, Any]] = []
    manifest_sources: list[tuple[str, str]] = []
    manifest_error = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            specs = manifest.get("agents", [])
            seen: set[str] = set()
            for spec in specs if isinstance(specs, list) else []:
                if not isinstance(spec, dict):
                    continue
                agent_id = str(spec.get("id", ""))
                seen.add(agent_id)
                entrypoint = str(spec.get("entrypoint", ""))
                entrypoint_exists = bool(entrypoint and (root / entrypoint).exists())
                sources = [str(s) for s in spec.get("sources", []) if isinstance(s, str)]
                for source_ref in sources:
                    manifest_sources.append((agent_id, source_ref))
                agents.append({
                    "id": agent_id,
                    "name": str(spec.get("name", "")),
                    "status": str(spec.get("status", "unknown")),
                    "entrypoint": entrypoint or None,
                    "entrypoint_exists": entrypoint_exists if entrypoint else None,
                    "declared_sources": sources,
                })
            ids = [a["id"] for a in agents]
            duplicates = sorted(k for k, count in Counter(ids).items() if count > 1)
            manifest_summary = {
                "path": repo_relative(manifest_path, root),
                "architecture_name": manifest.get("architecture_name"),
                "declared_count": len(agents),
                "unique_id_count": len(set(ids)),
                "duplicate_ids": duplicates,
                "status_counts": dict(Counter(a["status"] for a in agents)),
                "entrypoints_missing": [
                    a["id"] for a in agents if a["entrypoint"] and not a["entrypoint_exists"]
                ],
            }
        except (OSError, json.JSONDecodeError) as exc:
            manifest_error = f"{type(exc).__name__}: {exc}"
            manifest_summary = {"path": repo_relative(manifest_path, root), "error": manifest_error}
    else:
        manifest_summary = {"path": "agents/manifest.json", "error": "missing"}

    def has_manifest_owner(path: Path) -> list[str]:
        rel = repo_relative(path, root)
        owners: list[str] = []
        for agent_id, source_ref in manifest_sources:
            source_ref = re.split(r"\s+\(", source_ref, maxsplit=1)[0].strip().rstrip("/")
            # A declared module or directory keeps its subtree protected during migration.
            if source_ref and (rel == source_ref or rel.startswith(source_ref + "/")):
                owners.append(agent_id)
        return sorted(set(owners))

    layer_results: list[dict[str, Any]] = []
    for folder in layer_dirs(root):
        layer_files = sorted(folder.rglob("*.py"))
        inbound = sum(1 for p in layer_files if importers.get(p))
        layer_edges = [e for e in import_edges if e["from"].startswith(f"layers/{folder.name}/") or e["from"] == f"layers/{folder.name}"]
        layer_results.append({
            "name": folder.name,
            "python_file_count": len(layer_files),
            "files_with_static_inbound_imports": inbound,
            "cross_layer_import_edges_out": sum(
                1 for e in layer_edges
                if e["to"].startswith("layers/") and e["to"].split("/")[1] != folder.name
            ),
            "cross_layer_import_edges_in": sum(
                1 for e in import_edges
                if e["to"].startswith(f"layers/{folder.name}/") and e["from"].startswith("layers/")
                and e["from"].split("/")[1] != folder.name
            ),
            "agent_manifest_owners": sorted({
                owner for p in layer_files for owner in has_manifest_owner(p)
            }),
        })

    # Exact byte duplicates are objective candidates; no semantic equivalence is inferred.
    hashes: dict[str, list[str]] = defaultdict(list)
    function_hashes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path, tree in parsed.items():
        rel = repo_relative(path, root)
        if "/tests/" not in f"/{rel}" and not rel.startswith("tests/"):
            try:
                hashes[hashlib.sha256(path.read_bytes()).hexdigest()].append(rel)
            except OSError:
                pass
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) < 2:
                    continue
                normalized = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
                digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                owner = node.name
                function_hashes[digest].append({"path": rel, "symbol": owner, "line": str(node.lineno)})

    duplicate_files = [paths for paths in hashes.values() if len(paths) > 1]
    duplicate_bodies = [
        items for items in function_hashes.values()
        if len(items) > 1 and len({item["path"] for item in items}) > 1
    ]

    # References from the manifest are reported separately; they are not treated as proof
    # that a planned agent is already a live caller of a legacy module.
    orphan_candidates: list[dict[str, Any]] = []
    for path in files:
        rel = repo_relative(path, root)
        if not rel.startswith("layers/") or path.name == "__init__.py" or "/tests/" in f"/{rel}":
            continue
        if importers.get(path):
            continue
        owners = has_manifest_owner(path)
        orphan_candidates.append({
            "path": rel,
            "module": module_name(path, root),
            "manifest_owners": owners,
            "candidate_class": "planned_agent_source" if owners else "no_static_inbound_import_found",
            "warning": "Candidate only: dynamic imports, entry points, framework hooks and external callers may be invisible.",
        })

    provider_inventory: list[dict[str, Any]] = []
    for path in files:
        rel = repo_relative(path, root)
        lower = rel.lower()
        matched = [term for term in MODEL_PATH_TERMS if term in lower]
        if matched:
            provider_inventory.append({"path": rel, "categories": matched})

    source_count_by_layer = {
        row["name"]: row["python_file_count"] for row in layer_results
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "revision": os.environ.get("GITHUB_SHA", "local-or-unspecified"),
        "scope": {
            "python_roots": list(SOURCE_ROOTS) + ["main.py"],
            "layer_dirs_detected": len(layer_results),
            "method": "static AST imports plus manifest ownership; no runtime reachability claim",
        },
        "summary": {
            "layer_count": len(layer_results),
            "layer_python_files": sum(source_count_by_layer.values()),
            "scanned_python_files": len(files),
            "parse_errors": len(syntax_errors),
            "static_import_edges": len(import_edges),
            "exact_duplicate_file_groups": len(duplicate_files),
            "duplicate_function_body_groups": len(duplicate_bodies),
            "no_static_inbound_layer_module_candidates": len(orphan_candidates),
            "model_provider_related_files": len(provider_inventory),
        },
        "agent_manifest": manifest_summary,
        "agents": agents,
        "layers": layer_results,
        "import_edges": import_edges,
        "orphan_candidates": orphan_candidates,
        "exact_duplicate_file_groups": duplicate_files,
        "duplicate_function_body_groups": duplicate_bodies[:250],
        "model_provider_inventory": provider_inventory,
        "syntax_errors": syntax_errors,
        "safety_notes": [
            "This audit never deletes or edits source files.",
            "No-static-import and duplicate-body reports are leads for review, not deletion instructions.",
            "Dynamic imports, entry-point loading, reflection, framework registration, external callers and provider callbacks may not be visible statically.",
            "Model/provider adapters are inventoried explicitly so cleanup can preserve agent-building and inference capability.",
            "A cleanup deletion requires runtime ownership review, regression tests, integration evidence and rollback coverage.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="artifacts/ucos-architecture-audit.json")
    parser.add_argument("--fail-on-syntax-errors", action="store_true")
    args = parser.parse_args()
    report = build_report()
    output = (ROOT / args.json).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    print("AGENT_MANIFEST=" + json.dumps(report["agent_manifest"], sort_keys=True))
    print("LAYER_INVENTORY=" + json.dumps([
        {"name": layer["name"], "python_file_count": layer["python_file_count"]}
        for layer in report["layers"]
    ], sort_keys=True))
    print(f"AUDIT_JSON={repo_relative(output)}")
    if args.fail_on_syntax_errors and report["syntax_errors"]:
        print("SYNTAX_ERRORS=" + json.dumps(report["syntax_errors"], sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
