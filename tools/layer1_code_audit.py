#!/usr/bin/env python3
"""Deterministic static audit for Layer 1.

Produces a complete inventory of Layer 1 Python modules, classes and
functions/methods, plus import edges, intra/inter-module call candidates,
duplicate definitions, and conservative orphan candidates.

This is static evidence: dynamic dispatch/reflection/framework callbacks can
produce false orphan candidates, so candidates are never auto-deleted.
"""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
LAYER = ROOT / "layers" / "layer01_core"

def module_name(p: Path) -> str:
    return ".".join(p.relative_to(ROOT).with_suffix("").parts)

def norm_source(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=True, include_attributes=False)

def audit():
    files = sorted((LAYER / "modules").rglob("*.py"))
    modules = {}
    symbols = {}
    calls = []
    imports = []
    syntax_errors = []
    duplicate_hashes = defaultdict(list)

    for p in files:
        mod = module_name(p)
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as exc:
            syntax_errors.append({"module": mod, "error": str(exc)})
            continue
        classes, functions = [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                q = f"{mod}:{node.name}"
                classes.append(node.name)
                symbols[q] = {"kind": "class", "module": mod, "name": node.name,
                              "line": node.lineno}
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        mq = f"{mod}:{node.name}.{child.name}"
                        functions.append(f"{node.name}.{child.name}")
                        symbols[mq] = {"kind": "method", "module": mod,
                                       "class": node.name, "name": child.name,
                                       "line": child.lineno}
                        body = ast.Module(body=child.body, type_ignores=[])
                        duplicate_hashes[hashlib.sha256(norm_source(body).encode()).hexdigest()].append(mq)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not any(node in getattr(c, "body", []) for c in []):
                    # Class methods are already recorded above; this branch records
                    # module-level functions.
                    parent_class = next((c.name for c in ast.walk(tree)
                                         if isinstance(c, ast.ClassDef) and node in c.body), None)
                    if parent_class is None:
                        q = f"{mod}:{node.name}"
                        functions.append(node.name)
                        symbols[q] = {"kind": "function", "module": mod,
                                      "name": node.name, "line": node.lineno}
                        body = ast.Module(body=node.body, type_ignores=[])
                        duplicate_hashes[hashlib.sha256(norm_source(body).encode()).hexdigest()].append(q)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append({"module": mod, "line": node.lineno,
                                "text": ast.unparse(node)})
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append({"module": mod, "line": node.lineno, "callee": node.func.id})
                elif isinstance(node.func, ast.Attribute):
                    calls.append({"module": mod, "line": node.lineno,
                                  "callee": node.func.attr})

        modules[mod] = {"path": str(p.relative_to(ROOT)), "classes": classes,
                        "functions": functions}

    duplicate_groups = [v for v in duplicate_hashes.values() if len(v) > 1]
    defined_names = defaultdict(list)
    for q, s in symbols.items():
        defined_names[s["name"]].append(q)
    called_names = {c["callee"] for c in calls}
    orphan_candidates = []
    for q, s in symbols.items():
        if s["name"].startswith("_") or s["name"] in {"__init__", "__new__", "__enter__", "__exit__"}:
            continue
        if s["name"] not in called_names:
            orphan_candidates.append(q)

    report = {
        "scope": "layers/layer01_core/modules",
        "modules": modules,
        "symbols": symbols,
        "imports": imports,
        "calls": calls,
        "summary": {
            "module_count": len(modules),
            "class_count": sum(1 for s in symbols.values() if s["kind"] == "class"),
            "function_method_count": sum(1 for s in symbols.values() if s["kind"] in {"function", "method"}),
            "syntax_errors": len(syntax_errors),
            "duplicate_body_groups": len(duplicate_groups),
            "orphan_candidates": len(orphan_candidates),
        },
        "syntax_errors": syntax_errors,
        "duplicate_body_groups": duplicate_groups,
        "orphan_candidates": orphan_candidates,
        "limitations": [
            "Static AST call resolution cannot prove dynamic dispatch, reflection or external callers.",
            "Orphan candidates require runtime/coverage review before deletion.",
            "Duplicate bodies are candidates, not proof of duplicate responsibility.",
        ],
    }
    return report

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="layer1-code-audit.json")
    args = ap.parse_args()
    report = audit()
    out = ROOT / args.json
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    if report["syntax_errors"]:
        raise SystemExit(2)
