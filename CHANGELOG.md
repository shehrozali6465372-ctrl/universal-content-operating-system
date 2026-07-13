# 📋 Changelog

---

## [v0.1.1] - 2026-07-13

### Updated
- Module 1 (Config Manager) — Added immutable settings + config versioning
- `immutable_settings.py` — New file: defines read-only keys
- `config_manager.py` — set() blocks immutable keys, admin_mode override, CONFIG_VERSION
- Tests expanded: 15 → 24 (all passed)

---

## [v0.1.0] - 2026-07-13

### Added
- Initial project structure with 10-layer architecture
- Layer folders: layer01_core through layer10_monetization
- ROADMAP.md, CHANGELOG.md, VERSION
- Module 1: Config Manager (4 files + tests)
- Configuration schema with 3 required + 10 optional fields
- Custom validators and exceptions

---

## Upcoming

| Version | Module | Status |
|---------|--------|--------|
| v0.1.2 | Module 2: Secrets Manager | 🔜 Next |
| v0.1.3 | Module 3: Environment Loader | 🔜 |
| v0.1.4 | Module 4: Database Manager | 🔜 |
| v0.1.5 | Module 5: Memory Manager | 🔜 |
| v0.1.6 | Module 6: Logger | 🔜 |
| v0.1.7 | Module 7: Scheduler | 🔜 |
| v0.1.8 | Module 8: File Manager | 🔜 |
| v0.1.9 | Module 9: Settings Manager | 🔜 |
| v0.2.0 | Module 10: Backup & Recovery | 🔜 |
