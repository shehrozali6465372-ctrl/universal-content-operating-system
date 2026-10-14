from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs" / "architecture"
CEO = ARCH / "UCOS_CEO_AGENT_ARCHITECTURE_V1.md"
WORKERS = ARCH / "UCOS_SPECIALIST_AGENTS_AND_SYSTEM_GUARDIAN_V1.md"


def test_only_two_canonical_uaom_v1_architecture_documents_are_referenced():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert CEO.is_file()
    assert WORKERS.is_file()
    assert "docs/architecture/UCOS_CEO_AGENT_ARCHITECTURE_V1.md" in readme
    assert "docs/architecture/UCOS_SPECIALIST_AGENTS_AND_SYSTEM_GUARDIAN_V1.md" in readme
    assert not (ARCH / "UCOS_V1_2_PRODUCTION_CROSSCHECK.md").exists()
    assert not (ROOT / "docs" / "adr" / "001-layered-architecture.md").exists()


def test_frozen_architecture_keeps_exactly_seven_service_domains():
    text = CEO.read_text(encoding="utf-8")
    section = text.split("## 3. Frozen service boundary", 1)[1].split("## 4.", 1)[0]
    rows = re.findall(r"^\|\s*[1-7]\s*\|", section, flags=re.MULTILINE)
    assert len(rows) == 7
    assert "AI Worker Service" in section
    assert "Scheduler Service" in section
    assert "one deployed service per agent" in CEO.read_text(encoding="utf-8")


def test_canonical_roster_has_all_29_logical_roles():
    text = WORKERS.read_text(encoding="utf-8")
    section = text.split("## 2. Canonical roster", 1)[1].split("## 3.", 1)[0]
    roles = re.findall(r"^\|\s*(\d{1,2})\s*\|", section, flags=re.MULTILINE)
    assert [int(role) for role in roles] == list(range(1, 30))
    assert "System Guardian / Live Observability Agent" in section


def test_documents_are_design_frozen_not_false_production_certificates():
    for path in (CEO, WORKERS):
        text = path.read_text(encoding="utf-8")
        assert "FROZEN CANONICAL ARCHITECTURE" in text
        assert "NOT CERTIFIED" in text
        assert "not certified by this specification" in text.lower()
