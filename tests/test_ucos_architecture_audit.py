from __future__ import annotations

import json

from tools.ucos_architecture_audit import build_report


def test_audit_finds_cross_layer_imports_and_manifest_ownership(tmp_path):
    layer1 = tmp_path / "layers" / "layer01_core"
    layer2 = tmp_path / "layers" / "layer02_research"
    (layer1 / "__init__.py").parent.mkdir(parents=True)
    (layer2 / "__init__.py").parent.mkdir(parents=True)
    (layer1 / "__init__.py").write_text("", encoding="utf-8")
    (layer2 / "__init__.py").write_text("", encoding="utf-8")
    (layer1 / "core.py").write_text("def useful():\n    return 7\n", encoding="utf-8")
    (layer1 / "planned_source.py").write_text("def future_owner():\n    value = 1\n    return value\n", encoding="utf-8")
    (layer2 / "consumer.py").write_text(
        "from layers.layer01_core.core import useful\n\n"
        "def run():\n    return useful()\n",
        encoding="utf-8",
    )
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "manifest.json").write_text(
        json.dumps({
            "architecture_name": "test",
            "agents": [{
                "id": "AG01",
                "name": "test",
                "status": "planned",
                "sources": ["layers/layer01_core/planned_source.py"],
            }],
        }),
        encoding="utf-8",
    )

    report = build_report(tmp_path)
    by_name = {layer["name"]: layer for layer in report["layers"]}

    assert report["summary"]["layer_count"] == 2
    assert by_name["layer01_core"]["cross_layer_import_edges_in"] == 1
    assert by_name["layer02_research"]["cross_layer_import_edges_out"] == 1
    planned = next(item for item in report["orphan_candidates"] if item["path"] == "layers/layer01_core/planned_source.py")
    assert planned["candidate_class"] == "planned_agent_source"
    assert "may not be visible statically" in planned["warning"]


def test_unreferenced_code_is_only_reported_as_a_candidate(tmp_path):
    layer = tmp_path / "layers" / "layer01_core"
    layer.mkdir(parents=True)
    (layer / "__init__.py").write_text("", encoding="utf-8")
    (layer / "unused_candidate.py").write_text(
        "def candidate():\n    value = 1\n    return value\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path)
    candidate = next(
        item for item in report["orphan_candidates"]
        if item["path"] == "layers/layer01_core/unused_candidate.py"
    )
    assert candidate["candidate_class"] == "no_static_inbound_import_found"
    assert any("never deletes" in note for note in report["safety_notes"])
