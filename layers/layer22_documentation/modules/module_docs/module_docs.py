"""ModuleDocs — per-module documentation generation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ModuleDocumentation:
    def __init__(self, module_name: str, description: str = "") -> None:
        self.module_name = module_name
        self.description = description
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []

    def add_class(self, name: str, description: str, methods: Optional[List[str]] = None) -> None:
        self.classes.append({"name": name, "description": description, "methods": methods or []})

    def add_function(self, name: str, description: str, parameters: Optional[List[str]] = None) -> None:
        self.functions.append({"name": name, "description": description, "parameters": parameters or []})

    def generate(self) -> Dict[str, Any]:
        return {"module": self.module_name, "description": self.description,
                "classes": self.classes, "functions": self.functions}


class ModuleDocsRegistry:
    def __init__(self) -> None:
        self._docs: Dict[str, ModuleDocumentation] = {}

    def register(self, module_name: str, description: str = "") -> ModuleDocumentation:
        doc = ModuleDocumentation(module_name, description)
        self._docs[module_name] = doc
        return doc

    def get_doc(self, module_name: str) -> Optional[ModuleDocumentation]:
        return self._docs.get(module_name)

    def list_modules(self) -> List[str]:
        return list(self._docs.keys())

    def generate_all(self) -> List[Dict[str, Any]]:
        return [d.generate() for d in self._docs.values()]
