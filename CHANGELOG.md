# 📋 Changelog

## [v0.1.2] - 2026-07-13
### Added
- Module 2: Secrets Manager (Complete)
  - `secrets_manager.py` — Fernet encryption, store, retrieve, rotate
  - `key_store.py` — .secrets file management with 0600 permissions
  - `audit_logger.py` — Logs all actions, NEVER logs values
  - Health Check: master key, file, encryption, permissions
  - Key Rotation support
  - Bulk operations (store/retrieve multiple)
- Tests: 23/23 passed

## [v0.1.1] - 2026-07-13
### Updated
- Module 1: Immutable settings + config versioning

## [v0.1.0] - 2026-07-13
### Added
- Initial project structure, 10-layer architecture
