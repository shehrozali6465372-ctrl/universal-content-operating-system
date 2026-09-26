"""Production-safe image composition and layout planning."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

class CompositionRule:
    __slots__ = ("name","description","check_fn","metadata")
    def __init__(self, name: str, description: str = "") -> None:
        if not name or not name.strip():
            raise ValueError("rule name is required")
        self.name=name; self.description=description
        self.check_fn: Optional[Callable[["CompositionPlan"], bool]]=None
        self.metadata: Dict[str, Any]={}

class CompositionPlan:
    __slots__=("plan_id","layout","elements","dimensions","metadata")
    def __init__(self, layout: str="center", dimensions: Tuple[int,int]=(1080,1080)) -> None:
        if not layout or not layout.strip(): raise ValueError("layout is required")
        if (not isinstance(dimensions,tuple) or len(dimensions)!=2 or
            any(not isinstance(v,int) or isinstance(v,bool) or v<=0 for v in dimensions)):
            raise ValueError("dimensions must be a positive (width, height) tuple")
        self.plan_id=f"comp_{uuid.uuid4().hex}"; self.layout=layout
        self.elements: List[Dict[str,Any]]=[]; self.dimensions=dimensions; self.metadata={}
    def add_element(self, element_type: str, position: Tuple[int,int]=(0,0), size: Tuple[int,int]=(100,100)) -> None:
        if not element_type or not element_type.strip(): raise ValueError("element_type is required")
        if (not isinstance(position,tuple) or len(position)!=2 or
            any(not isinstance(v,int) or isinstance(v,bool) for v in position)):
            raise ValueError("position must be an integer (x, y) tuple")
        if (not isinstance(size,tuple) or len(size)!=2 or
            any(not isinstance(v,int) or isinstance(v,bool) or v<=0 for v in size)):
            raise ValueError("size must be a positive (width, height) tuple")
        self.elements.append({"type":element_type,"position":position,"size":size})
    def to_dict(self) -> Dict[str,Any]:
        return {"plan_id":self.plan_id,"layout":self.layout,"dimensions":self.dimensions,"elements":len(self.elements)}

class CompositionEngine:
    def __init__(self) -> None:
        self._rules: List[CompositionRule]=[]
        self._layouts={"center":{"alignment":"center","spacing":0},"grid":{"columns":3,"gutter":10},
                       "masonry":{"columns":2,"gutter":5},"stack":{"direction":"vertical","spacing":20}}
    def create_plan(self, layout: str="center", dimensions: Tuple[int,int]=(1080,1080)) -> CompositionPlan:
        if layout not in self._layouts: raise ValueError(f"unknown layout: {layout}")
        plan=CompositionPlan(layout,dimensions); plan.metadata["layout_config"]=dict(self._layouts[layout]); return plan
    def add_layout(self, name: str, config: Dict[str,Any]) -> None:
        if not name or not name.strip(): raise ValueError("layout name is required")
        if not isinstance(config,dict): raise TypeError("layout config must be a dictionary")
        self._layouts[name]=dict(config)
    def add_rule(self, rule: CompositionRule) -> None:
        if not isinstance(rule,CompositionRule): raise TypeError("rule must be a CompositionRule")
        self._rules.append(rule)
    def validate(self, plan: CompositionPlan) -> Dict[str,Any]:
        if not isinstance(plan,CompositionPlan): raise TypeError("plan must be a CompositionPlan")
        violations=[]; rule_errors=[]
        for rule in self._rules:
            if rule.check_fn is None: continue
            try: passed=bool(rule.check_fn(plan))
            except Exception as exc:
                rule_errors.append({"rule":rule.name,"error_type":type(exc).__name__,"error":str(exc)}); continue
            if not passed: violations.append(rule.name)
        return {"valid":not violations and not rule_errors,"violations":violations,"rule_errors":rule_errors}
    def list_layouts(self) -> List[str]: return list(self._layouts.keys())
