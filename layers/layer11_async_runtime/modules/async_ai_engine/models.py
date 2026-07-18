"""Models."""
from __future__ import annotations
import time
from typing import Any, Dict

class AIModel:
    __slots__ = ("model_id","name","status","config","metrics","created_at")
    def __init__(self) -> None:
        self.model_id = "aimodel_" + str(int(time.time()*1000))
        self.name = dict()
        self.status = time.time()
        self.config = dict()
        self.metrics = dict()
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {{k: getattr(self, k) for k in self.__slots__[:6]}}
