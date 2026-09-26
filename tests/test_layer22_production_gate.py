"""Production certification gate for Layer 22 documentation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from layers.layer22_documentation import APIDocumentation, ArchitectureDocs, DeveloperGuide


def test_api_documentation_contracts_and_isolation() -> None:
    docs = APIDocumentation("UCOS API", "6.0.0")
    parameters = [{"name": "q", "schema": {"type": "string"}}]
    response = {"ok": True, "nested": {"value": 1}}

    docs.add_endpoint("get", "/v1/search/{id}", "Search", parameters, response)
    parameters[0]["schema"]["type"] = "integer"
    response["nested"]["value"] = 99

    generated = docs.generate()
    assert generated["total_endpoints"] == 1
    assert generated["endpoints"][0]["method"] == "GET"
    assert generated["endpoints"][0]["parameters"][0]["schema"]["type"] == "string"
    assert generated["endpoints"][0]["response_example"]["nested"]["value"] == 1

    generated["endpoints"][0]["parameters"][0]["schema"]["type"] = "boolean"
    assert docs.list_endpoints()[0]["parameters"][0]["schema"]["type"] == "string"
    assert "## GET /v1/search/{id}" in docs.generate_markdown()

    with pytest.raises(ValueError, match="duplicate endpoint"):
        docs.add_endpoint("GET", "/v1/search/{id}")
    with pytest.raises(ValueError):
        docs.add_endpoint("TRACE", "/v1/search")
    with pytest.raises(ValueError):
        docs.add_endpoint("GET", "v1/search")
    with pytest.raises(TypeError):
        docs.add_endpoint("GET", "/v1/search", parameters=["bad"])  # type: ignore[list-item]


def test_architecture_documentation_is_complete_and_isolated() -> None:
    docs = ArchitectureDocs()
    docs.add_layer("Core", "Core runtime", 3)
    dependencies = ["Core"]
    docs.add_component("Docs", "Documentation runtime", dependencies)
    dependencies.append("Database")
    docs.add_decision("ADR-001", "accepted", "Use deterministic generation.")

    generated = docs.generate()
    assert generated["summary"] == {
        "total_layers": 1,
        "total_components": 1,
        "total_decisions": 1,
    }
    assert generated["components"][0]["dependencies"] == ["Core"]

    generated["components"][0]["dependencies"].append("Mutated")
    assert docs.generate()["components"][0]["dependencies"] == ["Core"]

    markdown = docs.generate_markdown()
    assert "## Decisions" in markdown
    assert "ADR-001" in markdown

    with pytest.raises(ValueError, match="duplicate layer"):
        docs.add_layer("Core", "Other")
    with pytest.raises(ValueError, match="duplicate component"):
        docs.add_component("Docs", "Other")
    with pytest.raises(ValueError, match="duplicate decision"):
        docs.add_decision("ADR-001", "rejected")


def test_developer_guide_is_deterministic_and_deduplicated() -> None:
    guide = DeveloperGuide()
    guide.add_section("Zeta", "z", 2)
    guide.add_section("Alpha", "a", 1)
    guide.add_section("Beta", "b", 1)
    guide.add_prerequisite("Python 3.12")
    guide.add_prerequisite("Python 3.12")
    guide.add_convention("Use type hints.")
    guide.add_convention("Use type hints.")

    generated = guide.generate()
    assert [item["title"] for item in generated["sections"]] == ["Alpha", "Beta", "Zeta"]
    assert generated["prerequisites"] == ["Python 3.12"]
    assert generated["conventions"] == ["Use type hints."]
    assert guide.generate_markdown().index("## Alpha") < guide.generate_markdown().index("## Beta")

    with pytest.raises(ValueError, match="duplicate section"):
        guide.add_section("Alpha", "duplicate")


def test_validation_rejects_invalid_architecture_and_guide_inputs() -> None:
    with pytest.raises(ValueError):
        ArchitectureDocs().add_layer("", "description")
    with pytest.raises(ValueError):
        ArchitectureDocs().add_layer("Core", "description", -1)
    with pytest.raises(TypeError):
        ArchitectureDocs().add_component("Docs", "description", ["", "Core"])  # type: ignore[list-item]
    with pytest.raises(ValueError):
        DeveloperGuide().add_section("Title", "", 0)
    with pytest.raises(ValueError):
        DeveloperGuide().add_section("Title", "content", True)  # type: ignore[arg-type]


def test_concurrent_api_registration_remains_consistent() -> None:
    docs = APIDocumentation()

    def add(index: int) -> None:
        docs.add_endpoint("GET", f"/v1/items/{index}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(add, range(40)))

    result = docs.generate()
    assert result["total_endpoints"] == 40
    assert len(result["endpoints"]) == 40
