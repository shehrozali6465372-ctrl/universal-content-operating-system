"""Validated configuration for the Layer 11 async runtime."""
from __future__ import annotations
from typing import Any, Dict, Mapping

class RuntimeConfig:
    __slots__=("max_workers","max_tasks","task_timeout","shutdown_timeout","health_check_interval","metrics_interval","max_retries","retry_delay","queue_size","batch_size","enable_profiling","enable_monitoring","log_level","metadata")
    def __init__(self)->None:
        self.max_workers=10
        self.max_tasks=1000
        self.task_timeout=300.0
        self.shutdown_timeout=30.0
        self.health_check_interval=30.0
        self.metrics_interval=60.0
        self.max_retries=3
        self.retry_delay=1.0
        self.queue_size=10000
        self.batch_size=50
        self.enable_profiling=False
        self.enable_monitoring=True
        self.log_level="INFO"
        self.metadata:Dict[str,Any]={}
        self.validate()
    def validate(self)->None:
        integer_fields=("max_workers","max_tasks","queue_size","batch_size")
        positive_fields=("task_timeout","shutdown_timeout","health_check_interval","metrics_interval")
        for name in integer_fields:
            value=getattr(self,name)
            if not isinstance(value,int) or isinstance(value,bool) or value<1:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.max_retries,int) or isinstance(self.max_retries,bool) or self.max_retries<0:
            raise ValueError("max_retries must be >= 0")
        if not isinstance(self.retry_delay,(int,float)) or isinstance(self.retry_delay,bool) or self.retry_delay<0:
            raise ValueError("retry_delay must be >= 0")
        for name in positive_fields:
            value=getattr(self,name)
            if not isinstance(value,(int,float)) or isinstance(value,bool) or value<=0:
                raise ValueError(f"{name} must be > 0")
        if not isinstance(self.log_level,str) or self.log_level.upper() not in {"DEBUG","INFO","WARNING","ERROR","CRITICAL"}:
            raise ValueError("invalid log_level")
        if not isinstance(self.metadata,dict):
            raise ValueError("metadata must be a dict")
    def to_dict(self)->Dict[str,Any]:
        return {name:getattr(self,name) for name in self.__slots__}
    @classmethod
    def from_dict(cls,data:Mapping[str,Any])->"RuntimeConfig":
        if not isinstance(data,Mapping):
            raise TypeError("data must be a mapping")
        unknown=set(data)-set(cls.__slots__)
        if unknown: raise ValueError(f"unknown configuration keys:
            {sorted(unknown)}")
        config=cls()
        for key,value in data.items():
            setattr(config,key,value)
        config.validate()
        return config
