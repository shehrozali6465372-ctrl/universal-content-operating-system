from __future__ import annotations

import json

from tools.ucos_architecture_audit import build_report, unowned_layer_modules


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
    assert "Candidate only" in planned["warning"]


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
    assert candidate["candidate_class"] == "no_static_production_inbound_import_found"
    assert any("never deletes" in note for note in report["safety_notes"])


def test_test_only_imports_do_not_count_as_production_ownership(tmp_path):
    layer = tmp_path / "layers" / "layer01_core"
    layer.mkdir(parents=True)
    (layer / "__init__.py").write_text("", encoding="utf-8")
    (layer / "legacy_candidate.py").write_text(
        "def old_helper(value):\n    normalized = str(value)\n    return normalized.strip()\n",
        encoding="utf-8",
    )
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_legacy.py").write_text(
        "from layers.layer01_core.legacy_candidate import old_helper\n"
        "def test_old_helper():\n    assert old_helper('x') == 'x'\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path)
    candidate = next(
        item for item in report["orphan_candidates"]
        if item["path"] == "layers/layer01_core/legacy_candidate.py"
    )
    layer_info = report["layers"][0]
    assert candidate["candidate_class"] == "tests_only_references"
    assert candidate["test_only_importer_count"] == 1
    assert layer_info["files_with_static_inbound_imports"] >= 1
    assert layer_info["files_with_static_production_inbound_imports"] == 0


def test_audit_flags_scaffold_that_claims_success_after_only_buffering(tmp_path):
    layer = tmp_path / "layers" / "layer11_async_runtime"
    layer.mkdir(parents=True)
    (layer / "__init__.py").write_text("", encoding="utf-8")
    (layer / "placeholder.py").write_text(
        "class Placeholder:\n"
        "    def __init__(self):\n"
        "        self._data = []\n"
        "    def process(self, data):\n"
        "        self._data.append(data)\n"
        "        return {'status': 'ok', 'processed': True}\n"
        "    def response(self, model):\n"
        "        return f'Response from {model}'\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path)
    patterns = report["scaffold_success_patterns"]
    assert any(
        item["path"] == "layers/layer11_async_runtime/placeholder.py"
        and item["pattern"] == "buffer_append_claims_processing_success"
        for item in patterns
    )
    assert any(
        item["path"] == "layers/layer11_async_runtime/placeholder.py"
        and item["pattern"] == "fabricated_runtime_output_string"
        for item in patterns
    )
    assert report["summary"]["scaffold_success_pattern_findings"] == 2


def test_audit_scans_service_sources_outside_known_layer_roots(tmp_path):
    layer = tmp_path / "layers" / "layer01_core"
    layer.mkdir(parents=True)
    (layer / "__init__.py").write_text("", encoding="utf-8")
    (layer / "runtime_api.py").write_text(
        "def health():\n    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    services = tmp_path / "services" / "content_api"
    services.mkdir(parents=True)
    (services / "server.py").write_text(
        "from layers.layer01_core.runtime_api import health\n"
        "def endpoint():\n    return health()\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path)
    target = next(
        item for item in report["import_edges"]
        if item["from"] == "services/content_api/server.py"
        and item["to"] == "layers/layer01_core/runtime_api.py"
    )
    assert target["from"].startswith("services/")
    layer_info = report["layers"][0]
    assert layer_info["files_with_static_production_inbound_imports"] >= 1


def test_audit_reports_missing_internal_imports(tmp_path):
    source = tmp_path / "services" / "content_api"
    source.mkdir(parents=True)
    (source / "server.py").write_text(
        "from layers.layer11_async_runtime.modules.background_workers.router import WorkerRouter\n"
        "def create():\n    return WorkerRouter()\n",
        encoding="utf-8",
    )
    (tmp_path / "layers" / "layer11_async_runtime" / "modules").mkdir(parents=True)
    (tmp_path / "layers" / "layer11_async_runtime" / "__init__.py").write_text(
        '"""Layer 11 test package."""\n', encoding="utf-8"
    )

    report = build_report(tmp_path)
    missing = [
        item for item in report["unresolved_internal_imports"]
        if item["path"] == "services/content_api/server.py"
    ]
    assert any(
        item["target"] == "layers.layer11_async_runtime.modules.background_workers.router"
        and item["kind"] == "production"
        for item in missing
    )
    assert report["summary"]["unresolved_internal_imports"] == len(
        report["unresolved_internal_imports"]
    )


def test_unowned_layer_gate_excludes_tested_and_manifest_owned_modules(tmp_path):
    layer = tmp_path / "layers" / "layer01_core"
    layer.mkdir(parents=True)
    (layer / "__init__.py").write_text("", encoding="utf-8")
    (layer / "unowned.py").write_text(
        "def unowned():\n    value = 1\n    return value\n", encoding="utf-8"
    )
    (layer / "tested.py").write_text(
        "def tested():\n    value = 2\n    return value\n", encoding="utf-8"
    )
    (layer / "shared.py").write_text(
        "def shared():\n    value = 3\n    return value\n", encoding="utf-8"
    )
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_tested.py").write_text(
        "from layers.layer01_core.tested import tested\n", encoding="utf-8"
    )
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "manifest.json").write_text(
        json.dumps({
            "agents": [{
                "id": "AG01", "status": "planned",
                "sources": ["layers/layer01_core/unowned.py"],
            }],
            "shared_components": [{
                "id": "SH01", "name": "Shared core",
                "sources": ["layers/layer01_core/shared.py"],
            }],
        }), encoding="utf-8"
    )

    report = build_report(tmp_path)
    assert unowned_layer_modules(report) == []
    manifest = json.loads((agents / "manifest.json").read_text(encoding="utf-8"))
    manifest["agents"][0]["sources"] = []
    (agents / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    report = build_report(tmp_path)
    assert [item["path"] for item in unowned_layer_modules(report)] == [
        "layers/layer01_core/unowned.py"
    ]
    assert report["agent_manifest"]["shared_component_count"] == 1
    shared = next(item for item in report["orphan_candidates"] if item["path"] == "layers/layer01_core/shared.py")
    assert shared["candidate_class"] == "shared_infrastructure"
    manifest["shared_components"] = []
    (agents / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    report = build_report(tmp_path)
    assert {item["path"] for item in unowned_layer_modules(report)} == {
        "layers/layer01_core/unowned.py", "layers/layer01_core/shared.py"
    }

def test_tests_helpers_are_not_counted_as_production_importers(tmp_path):
    layer = tmp_path / "layers" / "layer01_core"
    layer.mkdir(parents=True)
    (layer / "__init__.py").write_text("", encoding="utf-8")
    (layer / "helper.py").write_text(
        "def value():\n    return 1\n", encoding="utf-8"
    )
    helpers = tmp_path / "tests_helpers"
    helpers.mkdir()
    (helpers / "mock.py").write_text(
        "from layers.layer01_core.helper import value\n", encoding="utf-8"
    )

    report = build_report(tmp_path)
    edge = next(
        item for item in report["import_edges"]
        if item["from"] == "tests_helpers/mock.py"
        and item["to"] == "layers/layer01_core/helper.py"
    )
    assert edge["kind"] == "test"
    assert not any(
        item["from"] == "tests_helpers/mock.py"
        for item in report["production_import_edges"]
    )
