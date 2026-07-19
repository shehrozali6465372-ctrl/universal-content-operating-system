"""DocGenerator — auto-generate documentation for all layers."""
from __future__ import annotations
import os
import time
from typing import Any, Dict, List

class DocGenerator:
    def __init__(self, layers_dir: str = 'layers') -> None:
        self.layers_dir = layers_dir
        self._generated: List[Dict[str, Any]] = []

    def generate_layer_docs(self, layer_path: str) -> Dict[str, Any]:
        modules = []
        if os.path.exists(layer_path):
            for root, dirs, files in os.walk(layer_path):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for f in files:
                    if f.endswith('.py') and f != '__init__.py':
                        filepath = os.path.join(root, f)
                        rel_path = os.path.relpath(filepath, self.layers_dir)
                        modules.append({'file': f, 'path': rel_path,
                                         'size_bytes': os.path.getsize(filepath)})
        result = {'layer': os.path.basename(layer_path),
                  'modules': len(modules), 'details': modules,
                  'generated_at': time.time()}
        self._generated.append(result)
        return result

    def generate_all(self) -> List[Dict[str, Any]]:
        results = []
        for entry in os.listdir(self.layers_dir):
            path = os.path.join(self.layers_dir, entry)
            if os.path.isdir(path) and entry.startswith('layer'):
                results.append(self.generate_layer_docs(path))
        return results

    def api_docs(self, module_path: str) -> Dict[str, Any]:
        classes = []; functions = []
        try:
            with open(module_path) as f:
                content = f.read()
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('class ') and ':' in stripped:
                    name = stripped.split('(')[0].split(':')[0].replace('class ', '')
                    classes.append(name)
                elif stripped.startswith('def ') and '(' in stripped:
                    name = stripped.split('(')[0].replace('def ', '')
                    functions.append(name)
        except Exception: pass
        return {'classes': classes, 'functions': functions}

    def get_generated(self) -> List[Dict[str, Any]]:
        return list(self._generated)
