"""Models."""
from __future__ import annotations
import time
from typing import Any, Dict

class Plugin:
    __slots__ = ("plugin_id","name","status","config","version","created_at")
    def __init__(self) -> None:
        self.plugin_id = "plugin_" + str(int(time.time()*1000))
        self.name = dict()
        self.status = time.time()
        self.config = dict()
        self.version = dict()
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {{k: getattr(self, k) for k in self.__slots__[:6]}}
