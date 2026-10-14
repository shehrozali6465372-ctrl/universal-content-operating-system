from __future__ import annotations

import json

from layers.shared.json_store import atomic_write_json, load_json_object


def test_atomic_write_json_creates_parent_and_round_trips(tmp_path):
    target = tmp_path / "nested" / "state.json"
    atomic_write_json(target, {"version": 1, "items": [{"id": "a"}]})
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "version": 1,
        "items": [{"id": "a"}],
    }
    assert list(target.parent.glob("*.tmp")) == []


def test_load_json_object_returns_empty_for_missing_corrupt_or_non_object(tmp_path):
    assert load_json_object(None) == {}
    assert load_json_object(tmp_path / "missing.json") == {}

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{bad", encoding="utf-8")
    assert load_json_object(corrupt) == {}

    array = tmp_path / "array.json"
    array.write_text("[1, 2]", encoding="utf-8")
    assert load_json_object(array) == {}


def test_atomic_write_replaces_existing_file(tmp_path):
    target = tmp_path / "state.json"
    atomic_write_json(target, {"version": 1})
    atomic_write_json(target, {"version": 2})
    assert load_json_object(target) == {"version": 2}
