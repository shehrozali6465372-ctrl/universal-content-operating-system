"""GovernanceOrchestrator — full governance pipeline."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .ethics_engine import EthicsEngine
from .copyright_checker import CopyrightChecker
from .privacy_engine import PrivacyEngine
from .safety_policy import SafetyPolicy
from .policy_manager import PolicyManager
from .violation_tracker import ViolationTracker
from .governance_config import GovernanceConfig
from .governance_metrics import GovernanceMetrics
from .governance_events import GovernanceEvents
from .governance_health import GovernanceHealth
from .governance_validator import GovernanceValidator

class GovernanceOrchestrator:
    def __init__(self, config: Optional[GovernanceConfig] = None) -> None:
        self.config = config or GovernanceConfig()
        self.ethics = EthicsEngine()
        self.copyright = CopyrightChecker()
        self.privacy = PrivacyEngine()
        self.safety = SafetyPolicy()
        self.policies = PolicyManager()
        self.tracker = ViolationTracker()
        self.metrics = GovernanceMetrics()
        self.events = GovernanceEvents()
        self.health = GovernanceHealth()
        self.validator = GovernanceValidator()
        self._is_running = False
    def start(self) -> bool:
        self._is_running = True; self.events.publish("started"); return True
    def stop(self) -> bool:
        self._is_running = False; self.events.publish("stopped"); return True
    def check(self, content: str, checks: Optional[List[str]] = None) -> Dict[str, Any]:
        checks = checks or ["ethics", "copyright", "privacy", "safety"]
        results: List[Dict[str, Any]] = []
        engines = {"ethics": self.ethics, "copyright": self.copyright,
                   "privacy": self.privacy, "safety": self.safety}
        for check_type in checks:
            engine = engines.get(check_type)
            if engine:
                result = engine.check(content)
                result["type"] = check_type
                results.append(result)
                self.metrics.record(result["passed"], check_type)
        all_passed = all(r["passed"] for r in results)
        return {"all_passed": all_passed, "results": results,
                "total_checks": len(results)}
    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()
    def get_stats(self) -> Dict[str, Any]:
        return self.metrics.to_dict()
