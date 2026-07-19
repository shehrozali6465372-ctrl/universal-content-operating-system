"""BackupSystem — backup and restore Layer 13 data through the integration layer."""
from __future__ import annotations
import time
import json
import hashlib
from typing import Any, Dict, List, Optional

class BackupSystem:
    def __init__(self) -> None:
        self._backups: List[Dict[str, Any]] = []
        self._max_backups = 10

    def create_backup(self, data: Dict[str, Any], name: str = '') -> Dict[str, Any]:
        backup_id = hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()[:8]
        backup = {'id': backup_id, 'name': name or f'backup_{len(self._backups) + 1}',
                  'data': data, 'timestamp': time.time(),
                  'size': len(json.dumps(data, default=str))}
        self._backups.append(backup)
        if len(self._backups) > self._max_backups:
            self._backups = self._backups[-self._max_backups:]
        return {'id': backup_id, 'name': backup['name'], 'size': backup['size']}

    def restore(self, backup_id: str) -> Optional[Dict[str, Any]]:
        for b in self._backups:
            if b['id'] == backup_id: return b['data']
        return None

    def list_backups(self) -> List[Dict[str, Any]]:
        return [{'id': b['id'], 'name': b['name'], 'timestamp': b['timestamp'],
                'size': b['size']} for b in self._backups]

    def delete_backup(self, backup_id: str) -> bool:
        before = len(self._backups)
        self._backups = [b for b in self._backups if b['id'] != backup_id]
        return len(self._backups) < before
