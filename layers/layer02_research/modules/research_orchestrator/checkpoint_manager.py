"""
Checkpoint Manager
Layer 2: Research Engine — Module 10

Saves and restores execution state for resume-after-failure:
- Save checkpoint at each module completion
- Restore from last checkpoint
- Checkpoint integrity verification
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class CheckpointManager:
    """Manages execution checkpoints for crash recovery and resume."""

    def __init__(self, max_checkpoints: int = 50):
        self.max_checkpoints = max_checkpoints
        self._checkpoints: Dict[str, List[Dict]] = {}

    def save_checkpoint(
        self,
        execution_id: str,
        module: str,
        state: Dict[str, Any],
        completed_modules: Optional[List[str]] = None,
        confidence: float = 0.0,
    ) -> Dict:
        """Save a checkpoint for an execution."""
        if execution_id not in self._checkpoints:
            self._checkpoints[execution_id] = []

        checkpoint = {
            "checkpoint_id": f"cp_{execution_id}_{module}",
            "execution_id": execution_id,
            "module": module,
            "state": state,
            "completed_modules": completed_modules or [],
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Compute integrity hash
        checkpoint["integrity_hash"] = self._compute_hash(checkpoint)

        # Enforce max checkpoints
        checkpoints = self._checkpoints[execution_id]
        if len(checkpoints) >= self.max_checkpoints:
            checkpoints.pop(0)

        checkpoints.append(checkpoint)
        return checkpoint

    def get_last_checkpoint(self, execution_id: str) -> Optional[Dict]:
        """Get the most recent checkpoint for an execution."""
        checkpoints = self._checkpoints.get(execution_id, [])
        return checkpoints[-1] if checkpoints else None

    def get_checkpoint_at_module(self, execution_id: str, module: str) -> Optional[Dict]:
        """Get checkpoint for a specific module."""
        for cp in reversed(self._checkpoints.get(execution_id, [])):
            if cp["module"] == module:
                return cp
        return None

    def get_all_checkpoints(self, execution_id: str) -> List[Dict]:
        """Get all checkpoints for an execution."""
        return list(self._checkpoints.get(execution_id, []))

    def restore_from_checkpoint(self, execution_id: str) -> Optional[Dict]:
        """Restore state from the last valid checkpoint."""
        cp = self.get_last_checkpoint(execution_id)
        if not cp:
            return None

        if not self.verify_integrity(cp):
            return None

        return {
            "module": cp["module"],
            "state": cp["state"],
            "completed_modules": cp["completed_modules"],
            "confidence": cp["confidence"],
        }

    def verify_integrity(self, checkpoint: Dict) -> bool:
        """Verify checkpoint hasn't been tampered with."""
        stored_hash = checkpoint.get("integrity_hash", "")
        if not stored_hash:
            return False

        cp_copy = {k: v for k, v in checkpoint.items() if k != "integrity_hash"}
        computed = self._compute_hash(cp_copy)
        return stored_hash == computed

    def clear_checkpoints(self, execution_id: str):
        """Clear all checkpoints for an execution."""
        self._checkpoints.pop(execution_id, None)

    def get_module_to_resume_from(self, execution_id: str) -> Optional[str]:
        """Get the module to resume from based on last checkpoint."""
        cp = self.get_last_checkpoint(execution_id)
        if cp and self.verify_integrity(cp):
            return cp["module"]
        return None

    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA-256 hash of checkpoint data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
