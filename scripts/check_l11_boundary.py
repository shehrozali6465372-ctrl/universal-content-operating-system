from __future__ import annotations

import ast
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "layers"
layer = sys.argv[1]
target = root / layer
prefixes = (
    "layers.layer11_async_runtime.modules.async_",
    "layers.layer11_async_runtime.modules.background_",
    "layers.layer11_async_runtime.modules.concurrent_",
    "layers.layer11_async_runtime.modules.distributed_",
    "layers.layer11_async_runtime.modules.event_loop_",
)
violations = []
for path in target.rglob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
        for name in names:
            if name.startswith(prefixes):
                violations.append(f"{path}: {name}")
if violations:
    print("\n".join(violations))
    raise SystemExit(1)
print(f"{layer}: L11 legacy runtime boundary clean")
