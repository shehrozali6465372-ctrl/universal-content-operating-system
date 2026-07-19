"""DBAdapterInterface — abstract database adapter for all storage backends."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DBAdapterInterface(ABC):
    @abstractmethod
    def connect(self) -> bool: ...
    @abstractmethod
    def disconnect(self) -> bool: ...
    @abstractmethod
    def store(self, collection: str, data: Dict[str, Any]) -> str: ...
    @abstractmethod
    def retrieve(self, collection: str, key: str) -> Optional[Dict[str, Any]]: ...
    @abstractmethod
    def search(self, collection: str, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def update(self, collection: str, key: str, data: Dict[str, Any]) -> bool: ...
    @abstractmethod
    def delete(self, collection: str, key: str) -> bool: ...
    @abstractmethod
    def health(self) -> Dict[str, Any]: ...


class InMemoryDBAdapter(DBAdapterInterface):
    """In-memory adapter — fallback when no real DB available."""
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._is_connected = False

    def connect(self) -> bool: self._is_connected = True; return True
    def disconnect(self) -> bool: self._is_connected = False; return True

    def store(self, collection: str, data: Dict[str, Any]) -> str:
        self._store.setdefault(collection, {})
        key = str(len(self._store[collection]))
        self._store[collection][key] = data
        return key

    def retrieve(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        return self._store.get(collection, {}).get(key)

    def search(self, collection: str, query: Dict[str, Any],
               limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        for key, data in self._store.get(collection, {}).items():
            if all(data.get(k) == v for k, v in query.items()):
                results.append(data)
                if len(results) >= limit: break
        return results

    def update(self, collection: str, key: str, data: Dict[str, Any]) -> bool:
        if key in self._store.get(collection, {}):
            self._store[collection][key].update(data); return True
        return False

    def delete(self, collection: str, key: str) -> bool:
        if key in self._store.get(collection, {}):
            del self._store[collection][key]; return True
        return False

    def health(self) -> Dict[str, Any]:
        return {'status': 'healthy', 'type': 'in_memory',
                'collections': len(self._store),
                'total_records': sum(len(c) for c in self._store.values())}

    def count(self, collection: str) -> int:
        return len(self._store.get(collection, {}))
