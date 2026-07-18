"""Models."""
from __future__ import annotations
import time
from typing import Any, Dict

class HttpClient:
    __slots__ = ("client_id","name","status","config","metrics","created_at")
    def __init__(self) -> None:
        self.client_id = "httpclient_" + str(int(time.time()*1000))
        self.name = dict()
        self.status = time.time()
        self.config = dict()
        self.metrics = dict()
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {{k: getattr(self, k) for k in self.__slots__[:6]}}
